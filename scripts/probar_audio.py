#!/usr/bin/env python3
"""Prueba del audio del cliente (S7-L5). Uso: python3 scripts/probar_audio.py"""
import os
import sys

os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, "src/cliente")
import pygame
import juego as J
from sonido import Sonido, EFECTOS

fallos = 0


def chk(nombre, cond, extra=""):
    global fallos
    fallos += 0 if cond else 1
    print(f"{nombre:56s} {'OK' if cond else 'FALLA'} {extra}")


pygame.init()
chk("AUDIO del cliente empieza silencioso (no usa mixer)", not J.AUDIO.ok)
J.AUDIO.play("clic")
chk("play() sin activar no falla", True)
s = Sonido()
chk("activar() con los WAV del repo", s.activar(), "" if s.ok else "(revisa src/cliente/audio)")
chk("carga los 6 efectos y la musica", len(s.efectos) == len(EFECTOS) and s.musica is not None)
chk("musica_chaco dura mas de 30 s", s.musica is not None and s.musica.get_length() > 30,
    f"({s.musica.get_length():.1f} s)" if s.musica else "")
for n in EFECTOS:
    s.play(n)
chk("reproduce los 6 efectos sin error", True)
chk("M silencia", s.alternar() is True and s.musica.get_volume() == 0.0)
chk("M reactiva", s.alternar() is False and s.musica.get_volume() > 0.0)
pygame.mixer.quit()
t = Sonido()
chk("sin WAV: activar() devuelve False y no falla", t.activar("/no/existe") is False)
t.play("clic")
chk("play() en silencio no falla", True)
pygame.quit()
print("PRUEBA AUDIO: " + ("OK" if not fallos else f"{fallos} FALLA(S)"))
sys.exit(1 if fallos else 0)
