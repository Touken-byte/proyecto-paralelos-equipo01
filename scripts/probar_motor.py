#!/usr/bin/env python3
"""Prueba del servicio TCP del motor: arranca build/motor_tcp con mpirun, manda los comandos
y compara contra build/secuencial. Uso: python3 scripts/probar_motor.py [np=2] [puerto=5599]"""
import re
import socket
import subprocess
import sys
import time

import numpy as np

fallos = 0


def chk(nombre, cond, extra=""):
    global fallos
    if not cond:
        fallos += 1
    print(f"{nombre:54s} {'OK' if cond else 'FALLA'} {extra}")


class Cliente:
    def __init__(self, puerto, srv):
        for _ in range(150):
            if srv.poll() is not None:
                raise RuntimeError("el servidor termino antes de tiempo")
            try:
                self.s = socket.create_connection(("127.0.0.1", puerto), timeout=120)
                return
            except OSError:
                time.sleep(0.2)
        raise RuntimeError("no se pudo conectar al servidor")

    def enviar(self, t):
        self.s.sendall((t + "\n").encode())

    def linea(self):
        b = bytearray()
        while True:
            c = self.s.recv(1)
            if not c:
                raise ConnectionError("el servidor cerro la conexion")
            if c == b"\n":
                return b.decode()
            b += c

    def leer(self, n):
        b = bytearray()
        while len(b) < n:
            c = self.s.recv(min(65536, n - len(b)))
            if not c:
                raise ConnectionError("el servidor cerro la conexion")
            b += c
        return bytes(b)

    def estado(self, t):
        self.enviar(t)
        h = self.linea().split()
        if h[0] != "OK":
            return None
        w, hh = int(h[1]), int(h[2])
        n = w * hh
        e = dict(w=w, h=hh, hash=h[3], quemadas=int(h[4]), ardiendo=int(h[5]), paso=int(h[6]))
        e["terreno"], e["humedad"], e["actual"] = self.leer(n), self.leer(n), self.leer(n)
        return e

    def vigia(self, nsims, pasos):
        self.enviar(f"VIGIA {nsims} {pasos}")
        h = self.linea().split()
        if h[0] != "OK":
            return None
        n = int(h[1]) * int(h[2])
        return np.frombuffer(self.leer(4 * n), dtype="<u4"), h[4], float(h[5])


def ref(nivel, seed, pasos):
    o = subprocess.run(["build/secuencial", str(nivel), str(seed), str(pasos)],
                       capture_output=True, text=True).stdout
    m = re.search(r"hash=([0-9a-f]+) quemadas=(\d+)", o)
    return m.group(1), int(m.group(2))


def probar(cli, np_):
    e = cli.estado("LOAD_LEVEL 1 42")
    chk("LOAD_LEVEL 1: hash = secuencial (0 pasos)", e and (e["hash"], e["quemadas"]) == ref(1, 42, 0))
    chk("LOAD_LEVEL 1: mapa de 64x64", e and (e["w"], e["h"]) == (64, 64))
    cli.estado("SIMULATE 10")
    e = cli.estado("SIMULATE 10")
    chk("SIMULATE 10+10 (nivel 1): = secuencial 20 pasos", e and (e["hash"], e["quemadas"]) == ref(1, 42, 20) and e["paso"] == 20)
    cli.estado("LOAD_LEVEL 2 7")
    e = cli.estado("SIMULATE 60")
    chk("SIMULATE 60 (nivel 2, seed 7): = secuencial", e and (e["hash"], e["quemadas"]) == ref(2, 7, 60))
    e = cli.estado("LOAD_LEVEL 3 42")
    print("nivel 3: " + ("disponible" if e else "aun no disponible (se agrega en S7-L4)"))

    e = cli.estado("LOAD_LEVEL 2 42")
    w, hum0 = e["w"], e["humedad"]
    e = cli.estado("PLACE_TOOL pozo 20 20 3")
    chk("PLACE_TOOL pozo: centro es pozo y sube la humedad",
        e and e["terreno"][20 * w + 20] == 6 and e["humedad"][20 * w + 20] >= hum0[20 * w + 20])
    e = cli.estado("PLACE_TOOL cortafuego 30 40 3 h")
    chk("PLACE_TOOL cortafuego: 7 celdas en linea",
        e and all(e["terreno"][40 * w + x] in (4, 5) for x in range(27, 34)))
    chk("PLACE_TOOL brigada responde", cli.estado("PLACE_TOOL brigada 50 50 2") is not None)
    chk("PLACE_TOOL herramienta desconocida da ERR", cli.estado("PLACE_TOOL martillo 1 1") is None)
    chk("PLACE_TOOL fuera del mapa da ERR", cli.estado("PLACE_TOOL pozo 9999 1") is None)
    chk("WIND responde", cli.estado("WIND 0 1 2") is not None)
    chk("la conexion sigue viva tras los ERR", cli.estado("SIMULATE 1") is not None)

    cli.estado("LOAD_LEVEL 2 42")
    cli.estado("SIMULATE 5")
    h0 = cli.estado("SIMULATE 0")["hash"]
    r = cli.vigia(40, 30)
    chk("VIGIA 40x30: conteos validos", r and r[0].max() <= 40 and r[0].sum() > 0, f"({r[2]:.0f} ms)" if r else "")
    chk("VIGIA no altera el estado de la partida", cli.estado("SIMULATE 0")["hash"] == h0)
    r2 = cli.vigia(40, 30)
    chk("VIGIA repetido da el mismo hash", r and r2 and r[1] == r2[1])
    chk("VIGIA sin nivel/parametros malos da ERR", cli.vigia(0, 30) is None)
    if r:
        print(f"VIGIA_HASH={r[1]} np={np_}")


def main():
    np_ = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    puerto = int(sys.argv[2]) if len(sys.argv) > 2 else 5599
    srv = subprocess.Popen(["mpirun", "--oversubscribe", "--bind-to", "none", "--mca", "mpi_yield_when_idle", "1",
                            "-np", str(np_), "build/motor_tcp", str(puerto)])
    try:
        cli = Cliente(puerto, srv)
        probar(cli, np_)
        cli.enviar("STOP")
        cli.linea()
        srv.wait(timeout=30)
        chk("STOP apaga el servicio con codigo 0", srv.returncode == 0)
    finally:
        if srv.poll() is None:
            srv.kill()
    print(f"RESULTADO np={np_}: " + ("OK" if fallos == 0 else f"{fallos} FALLA(S)"))
    sys.exit(1 if fallos else 0)


main()
