#!/usr/bin/env python3
"""Prueba de la logica de animales y estrellas (S7-L3). Uso: python3 scripts/probar_animales.py"""
import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, "src/cliente")
import numpy as np
import pygame
import juego as J

fallos = 0


def chk(nombre, cond, extra=""):
    global fallos
    fallos += 0 if cond else 1
    print(f"{nombre:56s} {'OK' if cond else 'FALLA'} {extra}")


pygame.init()
pygame.display.set_mode((10, 10))
srv = J.lanzar_motor(2, 5598)
con = None
try:
    con = J.Conexion("127.0.0.1", 5598, srv)
    j = J.Juego(con, 1, 42)
    chk("nivel 1: 2 animales, peso total 2", len(j.animales) == 2 and j.rescatados()[1] == 2)
    chk("ningun animal empieza sobre agua", all(j.terreno[a["y"], a["x"]] != 4 for a in j.animales))
    for _ in range(50):
        j.paso_motor()
    chk("animales no alteran el fuego (hash = secuencial)", (j.e["hash"], j.e["quemadas"]) == J.ref(1, 42, 50))
    j.cerrar_nivel()
    chk("tras cerrar, nadie queda en 'normal'", all(a["est"] != "normal" for a in j.animales))
    chk("estrellas entre 0 y 3", 0 <= j.estrellas <= 3, f"(estrellas={j.estrellas}, rescatados={j.rescatados()}, quemado={j.porcentaje():.0f}%)")
    j.cargar()
    j.actual = np.zeros((j.h, j.w), np.uint8)
    j.e["ardiendo"], j.e["quemadas"] = 0, 0
    j.cerrar_nivel()
    chk("sin fuego: todos llegan a su refugio", j.rescatados() == (2, 2) and j.estrellas == 3)
    j.cargar()
    a = j.animales[0]
    j.actual = np.zeros((j.h, j.w), np.uint8)
    j.actual[a["y"], a["x"]] = 1
    j.mover_animales()
    chk("fuego sobre el animal: queda asustado", a["est"] == "asustado")
    for r, q, esp in (((9, 10), 20, 3), ((10, 10), 25, 2), ((8, 10), 30, 2), ((9, 10), 45, 1), ((5, 10), 80, 1), ((4, 10), 10, 0)):
        j.rescatados, j.porcentaje = (lambda r=r: r), (lambda q=q: q)
        chk(f"estrellas rescate {r[0]}/{r[1]}, quemado {q}%", j.calcular_estrellas() == esp, f"(esperado {esp})")
    del j.rescatados, j.porcentaje
    j.nivel = 2
    j.cargar()
    chk("nivel 2: animales fuera del agua", len(j.animales) == 2 and all(j.terreno[a["y"], a["x"]] != 4 for a in j.animales))
    j.cerrar_nivel()
    j.render(pygame.Surface((J.LW, J.LH)), 0, None)
    chk("la pantalla final se dibuja sin error", True)
    con.enviar("STOP")
    con.linea()
    srv.wait(timeout=30)
    chk("el motor se apaga con codigo 0", srv.returncode == 0)
finally:
    if srv.poll() is None:
        srv.kill()
    pygame.quit()
print("PRUEBA ANIMALES: " + ("OK" if fallos == 0 else f"{fallos} FALLA(S)"))
sys.exit(1 if fallos else 0)
