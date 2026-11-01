#!/usr/bin/env python3
"""Genera docs/evidencias/graficas/hoja_sprites.png (sprites x4 con etiquetas).
Uso: python3 scripts/hoja_sprites.py"""
import os
import sys
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, "src/cliente")
import pygame
from paleta import PALETA
from sprites import SPRITES

pygame.init()
ESC, PAD = 4, 10
C = 16 * ESC
CW, CH = C + PAD + 10, C + PAD + 16
fuente = pygame.font.Font(None, 15)


def superficie(filas):
    s = pygame.Surface((16, 16), pygame.SRCALPHA)
    for y, fila in enumerate(filas):
        for x, ch in enumerate(fila):
            if ch != ".":
                s.set_at((x, y), PALETA[int(ch, 16)])
    return pygame.transform.scale(s, (C, C))


celdas = []
for fila, d in enumerate(("abajo", "arriba", "derecha", "izquierda")):
    for f in range(3):
        celdas.append((f"guardiana_{d}_{f}", f, fila, f"{d} {f}"))
celdas.append(("guardiana_accion", 3, 0, "accion"))
for fila, a in enumerate(("loro", "zorro", "oso", "tatu", "tagua", "tortuga")):
    for col, est in enumerate(("normal", "asustado", "refugiado")):
        etq = f"{a} {est}" if col == 0 else est
        celdas.append((f"animal_{a}_{est}", 5 + col, fila, etq))

ancho = PAD + 8 * CW + PAD
alto = PAD + 6 * CH + PAD
hoja = pygame.Surface((ancho, alto))
hoja.fill((45, 40, 50))
for nombre, col, fila, etq in celdas:
    x, y = PAD + col * CW, PAD + fila * CH
    hoja.blit(superficie(SPRITES[nombre]), (x, y))
    hoja.blit(fuente.render(etq, True, (240, 240, 240)), (x, y + C + 2))

os.makedirs("docs/evidencias/graficas", exist_ok=True)
pygame.image.save(hoja, "docs/evidencias/graficas/hoja_sprites.png")
print(f"Hoja de {len(celdas)} sprites en docs/evidencias/graficas/hoja_sprites.png")
