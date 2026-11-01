"""Cliente minimo: dibuja el mapa en 320x180 escalado x4 y anima el fuego."""
import struct
import sys
import pygame
from paleta import PALETA
from tiles import TILES

ANCHO_L, ALTO_L, ESC = 320, 180, 4
TS = 16
# terreno (enum de mapa.h) -> tile; ribera/cortafuego/pozo se aproximan por ahora
T_A_TILE = {0: "pasto", 1: "monte", 2: "monte", 3: "pasto", 4: "agua", 5: "pasto", 6: "agua"}
E_SIN_QUEMAR, E_ARDIENDO, E_CENIZA = 0, 1, 2


def tile_a_superficie(filas):
    s = pygame.Surface((TS, TS))
    for y, fila in enumerate(filas):
        for x, ch in enumerate(fila):
            s.set_at((x, y), PALETA[int(ch, 16)])
    return s


def cargar(ruta):
    with open(ruta, "rb") as f:
        w, h = struct.unpack("ii", f.read(8))
        datos = f.read()
    n = w * h
    cuadros = len(datos) // n - 1
    estados = [datos[i * n:(i + 1) * n] for i in range(cuadros)]
    terreno = datos[cuadros * n:(cuadros + 1) * n]
    return w, h, estados, terreno


def main():
    ruta = sys.argv[1] if len(sys.argv) > 1 else "/tmp/nivel2.bin"
    w, h, estados, terreno = cargar(ruta)
    pygame.init()
    ventana = pygame.display.set_mode((ANCHO_L * ESC, ALTO_L * ESC))
    pygame.display.set_caption("Guardianes del Chaco")
    logica = pygame.Surface((ANCHO_L, ALTO_L))
    tiles = {k: tile_a_superficie(v) for k, v in TILES.items()}
    ceniza = pygame.Surface((TS, TS))
    ceniza.fill(PALETA[0xa])

    # Cada celda se dibuja 1 px; el mapa se centra. Los tiles se usan como textura.
    ox, oy = (ANCHO_L - w) // 2, (ALTO_L - h) // 2
    base = pygame.Surface((w, h))
    for y in range(h):
        for x in range(w):
            t = tiles[T_A_TILE.get(terreno[y * w + x], "pasto")]
            base.set_at((x, y), t.get_at((x % TS, y % TS)))

    reloj = pygame.time.Clock()
    paso, corriendo = 0, True
    while corriendo:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                corriendo = False
            elif ev.type == pygame.KEYDOWN and ev.key in (pygame.K_ESCAPE, pygame.K_q):
                corriendo = False
        frame = base.copy()
        est = estados[paso]
        for y in range(h):
            for x in range(w):
                e = est[y * w + x]
                if e == E_ARDIENDO:
                    frame.set_at((x, y), tiles["fuego"].get_at((x % TS, y % TS)))
                elif e == E_CENIZA:
                    frame.set_at((x, y), PALETA[0xa])
        logica.fill(PALETA[0])
        logica.blit(frame, (ox, oy))
        pygame.transform.scale(logica, ventana.get_size(), ventana)
        pygame.display.flip()
        paso = (paso + 1) % len(estados)
        reloj.tick(8)
    pygame.quit()


if __name__ == "__main__":
    main()
