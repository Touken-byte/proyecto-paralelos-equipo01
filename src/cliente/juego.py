#!/usr/bin/env python3
"""Cliente de Guardianes del Chaco conectado al motor por TCP (S7-L2).
Uso (desde la raiz del repo):
  python3 src/cliente/juego.py [--nivel 1] [--np 2] [--esc 4]   lanza el motor y juega
  python3 src/cliente/juego.py --host IP --puerto 5555          se conecta a un motor ya corriendo
  python3 src/cliente/juego.py --prueba                         prueba sin pantalla
Teclas: 1-4 herramienta, T orienta el cortafuego, V Vigia, Espacio simula la ronda, R reinicia, Esc sale."""
import argparse
import math
import os
import re
import socket
import subprocess
import sys
import time

if "--prueba" in sys.argv:
    os.environ["SDL_VIDEODRIVER"] = "dummy"
import numpy as np
import pygame

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, AQUI)
from paleta import PALETA  # noqa: E402
from sprites import SPRITES  # noqa: E402
from tiles import TILES  # noqa: E402

LW, LH, TS = 320, 180, 16
MAPA_X, MAPA_Y, MAPA_MAX, HUD_X = 4, 4, 172, 180
E_ARDIENDO, E_CENIZA = 1, 2
RONDAS, PA_RONDA, VIGIAS_RONDA, PASOS_RONDA, VEL = 5, 4, 2, 10, 140.0
ORDEN = ["cortafuego", "pozo", "brigada", "ribera"]
NOMBRES = {"cortafuego": "Cortafuego", "pozo": "Pozo", "brigada": "Brigada de agua", "ribera": "Bosque de ribera"}
COSTOS = {"cortafuego": 1, "pozo": 2, "brigada": 2, "ribera": 2}
RADIOS = {"cortafuego": 6, "pozo": 4, "brigada": 3, "ribera": 3}
COLOR_HERR = {"cortafuego": 3, "pozo": 0xe, "brigada": 0xf, "ribera": 9}
ANIMALES = {1: [("loro", (0.78, 0.25), (0.15, 0.15)), ("zorro", (0.2, 0.8), (0.85, 0.75))],
            2: [("oso", (0.35, 0.35), (0.1, 0.15)), ("tatu", (0.2, 0.7), (0.06, 0.85))],
            3: [("tagua", (0.7, 0.3), (0.2, 0.8)), ("tortuga", (0.3, 0.7), (0.8, 0.2))]}
# velocidad (celdas por paso), deteccion del fuego (celdas), peso en la cuenta de rescatados
PERFIL = {"loro": (1.2, 8, 1), "zorro": (1.1, 7, 1), "oso": (0.8, 6, 2),
          "tatu": (0.4, 5, 1), "tagua": (0.5, 6, 3), "tortuga": (0.2, 4, 1)}
PAL = np.array(PALETA, np.uint8)


def rgb(filas):
    a = np.zeros((TS, TS, 3), np.uint8)
    for y, f in enumerate(filas):
        for x, ch in enumerate(f):
            a[y, x] = PALETA[int(ch, 16)]
    return a


def recolor(filas, tabla):
    return ["".join(tabla.get(c, c) for c in f) for f in filas]


def construir_texturas():
    corta = ["".join("2" if (x * 7 + y * 3) % 11 == 0 else "3" for x in range(TS)) for y in range(TS)]
    pozo = ["".join("e" if (x + y) % 5 == 0 else "d" for x in range(TS)) for y in range(TS)]
    filas = [TILES["pasto"], recolor(TILES["monte"], {"7": "8", "6": "7"}),
             recolor(TILES["monte"], {"7": "6", "6": "1"}),
             recolor(TILES["pasto"], {"8": "7", "9": "e"}), TILES["agua"], corta, pozo]
    return np.stack([rgb(f) for f in filas])  # indice = enum Terreno de mapa.h


def envolver(fuente, texto, ancho):
    lineas, act = [], ""
    for p in texto.split():
        prueba = (act + " " + p).strip()
        if fuente.size(prueba)[0] <= ancho:
            act = prueba
        else:
            lineas.append(act)
            act = p
    lineas.append(act)
    return lineas


class Conexion:
    def __init__(self, host, puerto, srv=None):
        fin = time.time() + 40
        self.error = ""
        while True:
            if srv is not None and srv.poll() is not None:
                raise RuntimeError("el motor termino antes de tiempo")
            try:
                self.s = socket.create_connection((host, puerto), timeout=120)
                break
            except OSError:
                if time.time() > fin:
                    raise RuntimeError("no se pudo conectar al motor")
                time.sleep(0.2)

    def enviar(self, t):
        self.s.sendall((t + "\n").encode())

    def linea(self):
        b = bytearray()
        while True:
            c = self.s.recv(1)
            if not c:
                raise ConnectionError("el motor cerro la conexion")
            if c == b"\n":
                return b.decode()
            b += c

    def leer(self, n):
        b = bytearray()
        while len(b) < n:
            c = self.s.recv(min(65536, n - len(b)))
            if not c:
                raise ConnectionError("el motor cerro la conexion")
            b += c
        return bytes(b)

    def estado(self, cmd):
        self.enviar(cmd)
        h = self.linea().split()
        if h[0] != "OK" or len(h) < 7:
            self.error = " ".join(h[1:])
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
            self.error = " ".join(h[1:])
            return None
        n = int(h[1]) * int(h[2])
        return np.frombuffer(self.leer(4 * n), dtype="<u4"), h[4], float(h[5])


def lanzar_motor(np_, puerto):
    exe = os.path.join(RAIZ, "build", "motor_tcp")
    if not os.path.exists(exe):
        sys.exit("falta build/motor_tcp: ejecuta  make build/motor_tcp")
    return subprocess.Popen(["mpirun", "--oversubscribe", "--bind-to", "none", "--mca", "mpi_yield_when_idle", "1",
                             "-np", str(np_), exe, str(puerto)])


class Juego:
    def __init__(self, con, nivel, seed):
        self.con, self.nivel, self.seed = con, nivel, seed
        self.fuente = pygame.font.Font(None, 14)
        self.tex = construir_texturas()
        self.fuego = rgb(TILES["fuego"])
        self.sprites = {}
        self.herr, self.orient = "cortafuego", "h"
        self.botones = {h: pygame.Rect(HUD_X, 38 + 13 * i, 132, 11) for i, h in enumerate(ORDEN)}
        self.botones["vigia"] = pygame.Rect(HUD_X, 102, 132, 11)
        self.botones["simular"] = pygame.Rect(HUD_X, 115, 132, 11)
        self.terr_bytes = None
        self.cargar()

    # ---- estado ----
    def aplicar(self, e):
        self.e, self.w, self.h = e, e["w"], e["h"]
        self.actual = np.frombuffer(e["actual"], np.uint8).reshape(self.h, self.w)
        if e["terreno"] != self.terr_bytes:
            self.terr_bytes = e["terreno"]
            self.terreno = np.frombuffer(e["terreno"], np.uint8).reshape(self.h, self.w)
            ys = np.arange(self.h)[:, None] % TS
            xs = np.arange(self.w)[None, :] % TS
            self.base = self.tex[self.terreno, ys, xs]

    def cargar(self):
        e = self.con.estado(f"LOAD_LEVEL {self.nivel} {self.seed}")
        if e is None:
            raise RuntimeError(f"el motor no cargo el nivel {self.nivel}: {self.con.error}")
        self.terr_bytes = None
        self.aplicar(e)
        self.comb0 = int(np.isin(self.terreno, (0, 1, 2, 3)).sum())
        cs = max(1, MAPA_MAX // max(self.w, self.h))
        dw, dh = self.w * cs, self.h * cs
        if max(dw, dh) > MAPA_MAX:
            f = MAPA_MAX / max(dw, dh)
            dw, dh = int(dw * f), int(dh * f)
        self.disp = (dw, dh)
        self.ox, self.oy = MAPA_X + (MAPA_MAX - dw) // 2, MAPA_Y + (MAPA_MAX - dh) // 2
        self.mapa_rect = pygame.Rect(self.ox, self.oy, dw, dh)
        self.gx, self.gy, self.dir, self.fase = self.ox + 10.0, self.oy + dh - 4.0, "abajo", 0.0
        self.destino, self.accion, self.t_accion = None, None, 0.0
        self.ronda, self.pa, self.vigias = 1, PA_RONDA, VIGIAS_RONDA
        self.colocadas, self.prob = [], None
        self.cola_pasos, self.t_paso, self.fin, self.por_vigia = 0, 0.0, False, False
        self.msg = "Elige una herramienta y haz clic en el mapa."
        self.crear_animales()

    def porcentaje(self):
        return min(100.0, 100.0 * self.e["quemadas"] / max(1, self.comb0))

    # ---- acciones ----
    def clic_mapa(self, px, py):
        if self.fin or self.destino or self.accion or self.cola_pasos:
            return
        cx = int((px - self.ox) * self.w / self.disp[0])
        cy = int((py - self.oy) * self.h / self.disp[1])
        if not (0 <= cx < self.w and 0 <= cy < self.h):
            return
        if self.pa < COSTOS[self.herr]:
            self.msg = "No quedan puntos de accion. Pulsa Espacio para simular la ronda."
            return
        self.destino = (float(px), float(min(py + 5, self.oy + self.disp[1])))
        self.accion = (self.herr, cx, cy, self.orient)

    def ejecutar_accion(self):
        herr, cx, cy, ori = self.accion
        self.accion = None
        r = RADIOS[herr]
        cmd = f"PLACE_TOOL {herr} {cx} {cy} {r}" + (f" {ori}" if herr == "cortafuego" else "")
        e = self.con.estado(cmd)
        if e is None:
            self.msg = "El motor rechazo la herramienta: " + self.con.error
            return
        self.aplicar(e)
        self.pa -= COSTOS[herr]
        self.colocadas.append((herr, cx, cy, r))
        self.prob = None
        self.msg = f"{NOMBRES[herr]} colocado. Puntos de accion: {self.pa}."

    def simular_ronda(self):
        if self.fin or self.destino or self.accion or self.cola_pasos:
            return
        self.prob, self.cola_pasos, self.t_paso = None, PASOS_RONDA, 0.0
        self.msg = "Simulando la ronda..."

    def paso_motor(self):
        e = self.con.estado("SIMULATE 1")
        if e is None:
            raise RuntimeError("SIMULATE fallo: " + self.con.error)
        self.aplicar(e)
        self.mover_animales()

    def terminar_ronda(self):
        if self.e["ardiendo"] == 0 or self.ronda >= RONDAS:
            self.cerrar_nivel()
        else:
            self.ronda, self.pa, self.vigias = self.ronda + 1, PA_RONDA, VIGIAS_RONDA
            self.msg = f"Ronda {self.ronda}: planifica con tus {PA_RONDA} puntos."

    def consultar_vigia(self):
        if self.fin or self.destino or self.accion or self.cola_pasos:
            return
        if self.vigias <= 0:
            self.msg = "El Vigia ya no tiene usos en esta ronda."
            return
        self.por_vigia = True
        self.msg = "El Vigia esta calculando..."

    def ejecutar_vigia(self):
        self.por_vigia = False
        nsims = 200 if self.w * self.h <= 20000 else 100
        r = self.con.vigia(nsims, 30)
        if r is None:
            self.msg = "Error del Vigia: " + self.con.error
            return
        cuentas, _, ms = r
        self.prob = cuentas.reshape(self.h, self.w).astype(np.float32) / nsims
        self.vigias -= 1
        self.msg = f"Vigia: {nsims} simulaciones en {ms / 1000:.1f} s. Rojo = casi seguro que arde."

    def update(self, dt):
        if self.destino:
            dx, dy = self.destino[0] - self.gx, self.destino[1] - self.gy
            d = math.hypot(dx, dy)
            if d <= VEL * dt:
                self.gx, self.gy = self.destino
                self.destino, self.t_accion = None, 0.25
            else:
                self.gx += dx / d * VEL * dt
                self.gy += dy / d * VEL * dt
                self.fase += dt * 8
                if abs(dx) > abs(dy):
                    self.dir = "derecha" if dx > 0 else "izquierda"
                else:
                    self.dir = "abajo" if dy > 0 else "arriba"
        elif self.accion:
            self.t_accion -= dt
            if self.t_accion <= 0:
                self.ejecutar_accion()
        if self.cola_pasos:
            self.t_paso += dt
            if self.t_paso >= 0.12:
                self.t_paso = 0.0
                self.paso_motor()
                self.cola_pasos -= 1
                if self.cola_pasos == 0:
                    self.terminar_ronda()

    # ---- dibujo ----
    def sprite(self, clave):
        s = self.sprites.get(clave)
        if s is None:
            s = pygame.Surface((TS, TS), pygame.SRCALPHA)
            for y, f in enumerate(SPRITES[clave]):
                for x, ch in enumerate(f):
                    if ch != ".":
                        s.set_at((x, y), PALETA[int(ch, 16)])
            self.sprites[clave] = s
        return s

    def superficie_mapa(self, fr):
        img = self.base.copy()
        arde = self.actual == E_ARDIENDO
        if arde.any():
            ys = (np.arange(self.h)[:, None] + fr) % TS
            xs = np.arange(self.w)[None, :] % TS
            img[arde] = self.fuego[ys, xs][arde]
        img[self.actual == E_CENIZA] = PAL[1]
        if self.prob is not None:
            p = self.prob
            a = (0.85 * np.power(p, 0.6))[..., None]
            col = np.stack([np.full_like(p, 255), 230 * (1 - p), np.full_like(p, 40)], axis=-1)
            img = (img * (1 - a) + col * a).astype(np.uint8)
        sup = pygame.surfarray.make_surface(np.ascontiguousarray(img.swapaxes(0, 1)))
        return pygame.transform.scale(sup, self.disp)

    # ---- animales (RF-04) y estrellas (RF-08) ----
    def libre(self, fx, fy):
        cx, cy = int(fx * (self.w - 1)), int(fy * (self.h - 1))
        for r in range(12):
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    x, y = cx + dx, cy + dy
                    if 0 <= x < self.w and 0 <= y < self.h and self.terreno[y, x] != 4:
                        return x, y
        return cx, cy

    def crear_animales(self):
        self.animales = []
        for nombre, ini, ref in ANIMALES.get(self.nivel, []):
            vel, det, peso = PERFIL[nombre]
            x, y = self.libre(*ini)
            self.animales.append(dict(nombre=nombre, x=x, y=y, ref=self.libre(*ref), vel=vel,
                                      det=det, peso=peso, acc=0.0, est="normal"))
        self.estrellas = 0

    def rescatados(self):
        total = sum(a["peso"] for a in self.animales)
        return sum(a["peso"] for a in self.animales if a["est"] == "refugiado"), total

    def paso_animal(self, a, arde, quem):
        rx_, ry_ = a["ref"]
        x, y, r = a["x"], a["y"], a["det"]
        if math.hypot(rx_ - x, ry_ - y) <= 1.5:
            a["x"], a["y"], a["est"] = rx_, ry_, "refugiado"
            return
        y0, y1, x0, x1 = max(0, y - r), min(self.h, y + r + 1), max(0, x - r), min(self.w, x + r + 1)
        fy, fx = np.nonzero(arde[y0:y1, x0:x1])
        fx, fy = fx + x0, fy + y0
        mejor, mc = None, 1e9
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                nx, ny = x + dx, y + dy
                if (dx == 0 and dy == 0) or not (0 <= nx < self.w and 0 <= ny < self.h):
                    continue
                if quem[ny, nx] or (a["nombre"] != "loro" and self.terreno[ny, nx] == 4):
                    continue
                c = math.hypot(rx_ - nx, ry_ - ny)
                if len(fx):
                    d = float(np.min(np.hypot(fx - nx, fy - ny)))
                    if d < r:
                        c += 4.0 * (r - d)
                if c < mc:
                    mc, mejor = c, (nx, ny)
        if mejor:
            a["x"], a["y"] = mejor

    def mover_animales(self):
        arde, quem = self.actual == E_ARDIENDO, self.actual != 0
        for a in self.animales:
            if a["est"] != "normal":
                continue
            if quem[a["y"], a["x"]]:
                a["est"] = "asustado"
                continue
            a["acc"] += a["vel"]
            while a["acc"] >= 1.0 and a["est"] == "normal":
                a["acc"] -= 1.0
                self.paso_animal(a, arde, quem)

    def calcular_estrellas(self):
        r, t = self.rescatados()
        pr = 100.0 * r / t if t else 100.0
        q = self.porcentaje()
        if pr >= 90 and q < 25:
            return 3
        if pr >= 75 and q < 40:
            return 2
        return 1 if pr >= 50 else 0

    def cerrar_nivel(self):
        self.fin = True
        if self.e["ardiendo"] == 0:
            for _ in range(600):
                if all(a["est"] != "normal" for a in self.animales):
                    break
                self.mover_animales()
        for a in self.animales:
            if a["est"] == "normal":
                a["est"] = "asustado"
        self.estrellas = self.calcular_estrellas()
        r, t = self.rescatados()
        self.msg = f"{self.estrellas} estrellas. Rescatados {r}/{t}. R para reintentar."

    def estrella(self, lg, cx, cy, r, llena):
        pts = [(cx + (r if k % 2 == 0 else r * 0.45) * math.cos(-math.pi / 2 + k * math.pi / 5),
                cy + (r if k % 2 == 0 else r * 0.45) * math.sin(-math.pi / 2 + k * math.pi / 5)) for k in range(10)]
        pygame.draw.polygon(lg, PALETA[0xc if llena else 1], pts)
        pygame.draw.polygon(lg, PALETA[0xb if llena else 0], pts, 1)

    def pantalla_final(self, lg):
        r = pygame.Rect(self.ox + 6, self.oy + self.disp[1] // 2 - 40, self.disp[0] - 12, 80)
        pygame.draw.rect(lg, PALETA[0], r)
        pygame.draw.rect(lg, PALETA[0xc], r, 1)
        self.txt(lg, "NIVEL TERMINADO", r.x + 8, r.y + 5, 0xc)
        for i in range(3):
            self.estrella(lg, r.x + r.w // 2 - 30 + i * 30, r.y + 30, 11, i < self.estrellas)
        rs, tt = self.rescatados()
        self.txt(lg, f"Resc {rs}/{tt}  Quemado {self.porcentaje():.0f}%", r.x + 8, r.y + 52)
        self.txt(lg, "R reintentar", r.x + 8, r.y + 65, 4)

    def asustado(self, fx, fy):
        cx, cy, r = int(fx * self.w), int(fy * self.h), 6
        sub = self.actual[max(0, cy - r):cy + r + 1, max(0, cx - r):cx + r + 1]
        return bool((sub == E_ARDIENDO).any())

    def txt(self, lg, s, x, y, c=5):
        lg.blit(self.fuente.render(s, False, PALETA[c]), (x, y))

    def render(self, lg, fr, hover):
        lg.fill(PALETA[0])
        lg.blit(self.superficie_mapa(fr), (self.ox, self.oy))
        pxc = self.disp[0] / self.w
        for herr, cx, cy, r in self.colocadas:
            if herr != "cortafuego":
                c = (int(self.ox + (cx + 0.5) * pxc), int(self.oy + (cy + 0.5) * self.disp[1] / self.h))
                pygame.draw.circle(lg, PALETA[COLOR_HERR[herr]], c, max(2, int(r * pxc)), 1)
        if hover and self.mapa_rect.collidepoint(hover) and not self.fin:
            r, col = RADIOS[self.herr], PALETA[COLOR_HERR[self.herr]]
            if self.herr == "cortafuego":
                L = (2 * r + 1) * pxc
                rect = (hover[0] - L / 2, hover[1] - pxc / 2, L, max(pxc, 1)) if self.orient == "h" \
                    else (hover[0] - pxc / 2, hover[1] - L / 2, max(pxc, 1), L)
                pygame.draw.rect(lg, col, pygame.Rect(rect), 1)
            else:
                pygame.draw.circle(lg, col, hover, max(2, int(r * pxc)), 1)
        figuras = []
        for a in self.animales:
            rx_, ry_ = a["ref"]
            pygame.draw.circle(lg, PALETA[0xc], (int(self.ox + (rx_ + 0.5) * pxc), int(self.oy + (ry_ + 0.5) * self.disp[1] / self.h)), 3, 1)
        for a in self.animales:
            qx = self.ox + (a["x"] + 0.5) * pxc
            qy = self.oy + (a["y"] + 0.5) * self.disp[1] / self.h
            spr = self.sprite(f"animal_{a['nombre']}_{a['est']}")
            figuras.append((qy, spr, (qx - 8, qy - 14)))
            if a["nombre"] == "tagua":
                figuras.append((qy + 1, spr, (qx - 13, qy - 12)))
                figuras.append((qy + 1, spr, (qx + 5, qy - 12)))
        if self.accion and not self.destino:
            g = self.sprite("guardiana_accion")
        else:
            seq = (1, 0, 2, 0)
            g = self.sprite(f"guardiana_{self.dir}_{seq[int(self.fase) % 4] if self.destino else 0}")
        figuras.append((self.gy, g, (int(self.gx) - 8, int(self.gy) - 15)))
        for _, s, pos in sorted(figuras, key=lambda t: t[0]):
            lg.blit(s, (int(pos[0]), int(pos[1])))
        self.hud(lg)
        if self.fin:
            self.pantalla_final(lg)

    def hud(self, lg):
        self.txt(lg, "GUARDIANES DEL CHACO", HUD_X, 4, 0xc)
        self.txt(lg, f"Nivel {self.nivel}  Ronda {self.ronda}/{RONDAS}  Resc {self.rescatados()[0]}/{self.rescatados()[1]}", HUD_X, 15)
        self.txt(lg, f"Acciones {self.pa}/{PA_RONDA}  Vigia {self.vigias}/{VIGIAS_RONDA}", HUD_X, 25)
        for i, h in enumerate(ORDEN):
            r = self.botones[h]
            pygame.draw.rect(lg, PALETA[2 if h == self.herr else 1], r)
            pygame.draw.rect(lg, PALETA[COLOR_HERR[h]], (r.x + 2, r.y + 2, 7, 7))
            self.txt(lg, f"{i + 1} {NOMBRES[h]} {COSTOS[h]}pa", r.x + 12, r.y + 1)
        self.txt(lg, "Cortafuego: " + ("horizontal" if self.orient == "h" else "vertical") + "  tecla T", HUD_X, 90, 4)
        for clave, etq in (("vigia", "V  Consultar al Vigia"), ("simular", "Espacio  Simular ronda")):
            r = self.botones[clave]
            pygame.draw.rect(lg, PALETA[6], r)
            self.txt(lg, etq, r.x + 3, r.y + 1)
        if self.prob is not None:
            for i in range(60):
                p = i / 59
                lg.fill((255, int(230 * (1 - p)), 40), (HUD_X + 14 + i, 128, 1, 4))
            self.txt(lg, "0%", HUD_X, 126, 4)
            self.txt(lg, "100%", HUD_X + 78, 126, 4)
        self.txt(lg, f"Quemado {self.porcentaje():.0f}%   Llamas {self.e['ardiendo']}", HUD_X, 135)
        for i, ln in enumerate(envolver(self.fuente, self.msg, LW - HUD_X - 4)[:3]):
            self.txt(lg, ln, HUD_X, 148 + 10 * i, 0xc if self.fin else 4)


def cerrar(con, srv):
    try:
        if con is not None:
            con.enviar("STOP" if srv is not None else "QUIT")
            con.linea()
        if srv is not None:
            srv.wait(timeout=10)
    except Exception:
        pass
    if srv is not None and srv.poll() is None:
        srv.kill()


def jugar(a):
    pygame.init()
    ventana = pygame.display.set_mode((LW * a.esc, LH * a.esc))
    pygame.display.set_caption("Guardianes del Chaco")
    lg = pygame.Surface((LW, LH))
    srv = None if a.host else lanzar_motor(a.np, a.puerto)
    con = None
    try:
        con = Conexion(a.host or "127.0.0.1", a.puerto, srv)
        j = Juego(con, a.nivel, a.seed)
        reloj, t, corriendo = pygame.time.Clock(), 0.0, True
        teclas = {pygame.K_1: "cortafuego", pygame.K_2: "pozo", pygame.K_3: "brigada", pygame.K_4: "ribera"}
        while corriendo:
            dt = min(reloj.tick(30) / 1000.0, 0.1)
            t += dt
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    corriendo = False
                elif ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_ESCAPE, pygame.K_q):
                        corriendo = False
                    elif ev.key in teclas:
                        j.herr = teclas[ev.key]
                    elif ev.key == pygame.K_t:
                        j.orient = "v" if j.orient == "h" else "h"
                    elif ev.key == pygame.K_v:
                        j.consultar_vigia()
                    elif ev.key == pygame.K_SPACE:
                        j.simular_ronda()
                    elif ev.key == pygame.K_r:
                        j.cargar()
                elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    p = (ev.pos[0] // a.esc, ev.pos[1] // a.esc)
                    if j.mapa_rect.collidepoint(p):
                        j.clic_mapa(*p)
                    else:
                        for h in ORDEN:
                            if j.botones[h].collidepoint(p):
                                j.herr = h
                        if j.botones["vigia"].collidepoint(p):
                            j.consultar_vigia()
                        if j.botones["simular"].collidepoint(p):
                            j.simular_ronda()
            j.update(dt)
            mx, my = pygame.mouse.get_pos()
            j.render(lg, int(t * 6), (mx // a.esc, my // a.esc))
            pygame.transform.scale(lg, ventana.get_size(), ventana)
            pygame.display.flip()
            if j.por_vigia:
                j.ejecutar_vigia()
    finally:
        cerrar(con, srv)
        pygame.quit()


def ref(nivel, seed, pasos):
    o = subprocess.run([os.path.join(RAIZ, "build", "secuencial"), str(nivel), str(seed), str(pasos)],
                       capture_output=True, text=True).stdout
    m = re.search(r"hash=([0-9a-f]+) quemadas=(\d+)", o)
    return m.group(1), int(m.group(2))


def prueba(a):
    pygame.init()
    ventana = pygame.display.set_mode((LW * a.esc, LH * a.esc))
    lg = pygame.Surface((LW, LH))
    fallos = []

    def chk(nombre, cond):
        print(f"{nombre:52s} {'OK' if cond else 'FALLA'}")
        if not cond:
            fallos.append(nombre)

    def foto(nombre):
        pygame.transform.scale(lg, ventana.get_size(), ventana)
        pygame.image.save(ventana, nombre)
        chk(f"imagen {nombre}", os.path.getsize(nombre) > 5000)

    srv = lanzar_motor(a.np, a.puerto)
    con = None
    try:
        con = Conexion("127.0.0.1", a.puerto, srv)
        j = Juego(con, 1, 42)
        chk("nivel 1 cargado (64x64)", (j.w, j.h) == (64, 64))
        for _ in range(10):
            j.paso_motor()
        chk("10 pasos del cliente = secuencial", (j.e["hash"], j.e["quemadas"]) == ref(1, 42, 10))
        j.cargar()
        ys, xs = np.nonzero(j.actual == E_ARDIENDO)
        cx, cy = min(j.w - 8, int(xs[0]) + 8), int(ys[0])
        px = int(j.ox + (cx + 0.5) * j.disp[0] / j.w)
        py = int(j.oy + (cy + 0.5) * j.disp[1] / j.h)
        j.herr, j.orient = "cortafuego", "v"
        j.clic_mapa(px, py)
        for _ in range(400):
            j.update(0.05)
            if not j.destino and not j.accion:
                break
        chk("cortafuego colocado con clic y guardiana", (j.terreno[max(0, cy - 6):cy + 7, cx] == 5).sum() >= 1 and j.pa == 3)
        j.simular_ronda()
        for _ in range(100):
            j.update(0.2)
            if not j.cola_pasos:
                break
        chk("ronda animada de 10 pasos", j.e["paso"] == PASOS_RONDA and (j.ronda == 2 or j.fin))
        j.render(lg, 0, None)
        foto("/tmp/cliente_prueba_ronda.png")
        j.consultar_vigia()
        j.ejecutar_vigia()
        chk("Vigia: probabilidades entre 0 y 1", j.prob is not None and 0 < j.prob.max() <= 1.0)
        j.render(lg, 0, None)
        foto("/tmp/cliente_prueba_vigia.png")
        con.enviar("STOP")
        con.linea()
        srv.wait(timeout=30)
        chk("el motor se apaga con codigo 0", srv.returncode == 0)
    finally:
        if srv.poll() is None:
            srv.kill()
        pygame.quit()
    print("PRUEBA CLIENTE: " + ("OK" if not fallos else f"{len(fallos)} FALLA(S)"))
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--nivel", type=int, default=1)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--np", type=int, default=2)
    ap.add_argument("--puerto", type=int, default=5555)
    ap.add_argument("--host", default=None)
    ap.add_argument("--esc", type=int, default=4)
    ap.add_argument("--prueba", action="store_true")
    args = ap.parse_args()
    prueba(args) if args.prueba else jugar(args)
