#!/usr/bin/env python3
"""Prueba del nivel 3 (S7-L4). Uso: python3 scripts/probar_nivel3.py [np=2] [puerto=5597]"""
import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, "src/cliente")
import pygame
import juego as J

NP = int(sys.argv[1]) if len(sys.argv) > 1 else 2
PUERTO = int(sys.argv[2]) if len(sys.argv) > 2 else 5597
fallos = 0


def chk(nombre, cond, extra=""):
    global fallos
    fallos += 0 if cond else 1
    print(f"{nombre:56s} {'OK' if cond else 'FALLA'} {extra}")


pygame.init()
pygame.display.set_mode((10, 10))
srv = J.lanzar_motor(NP, PUERTO)
con = None
try:
    con = J.Conexion("127.0.0.1", PUERTO, srv)
    j = J.Juego(con, 3, 42)
    chk("nivel 3 cargado (200x200)", (j.w, j.h) == (200, 200))
    chk("ningun animal empieza sobre agua", all(j.terreno[a["y"], a["x"]] != 4 for a in j.animales))
    llegada = {}
    for t in range(1, 301):
        j.mover_animales()
        for a in j.animales:
            if a["est"] == "refugiado" and a["nombre"] not in llegada:
                llegada[a["nombre"]] = t
        if len(llegada) == len(j.animales):
            break
    for a in j.animales:
        n = a["nombre"]
        chk(f"{n} llega a su refugio en <= 45 pasos sin fuego", n in llegada and llegada[n] <= 45,
            f"(pasos={llegada.get(n)}, estado={a['est']})")
    j.cargar()
    e = con.estado("SIMULATE 50")
    r = J.ref(3, 42, 50)
    chk(f"hash a 50 pasos = secuencial (np={NP})", e is not None and (e["hash"], e["quemadas"]) == r,
        f"motor={(e['hash'], e['quemadas']) if e else None} sec={r}")
    con.enviar("STOP")
    con.linea()
    srv.wait(timeout=30)
    chk("el motor se apaga con codigo 0", srv.returncode == 0)
finally:
    if srv.poll() is None:
        srv.kill()
    pygame.quit()
print("PRUEBA NIVEL 3: " + ("OK" if not fallos else f"{fallos} FALLA(S)"))
sys.exit(1 if fallos else 0)
