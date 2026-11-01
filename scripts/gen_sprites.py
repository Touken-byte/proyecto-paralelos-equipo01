#!/usr/bin/env python3
"""Genera src/cliente/sprites.py: sprites 16x16 como texto ('.' = transparente, resto = indice hex de paleta).
Uso: python3 scripts/gen_sprites.py"""


def lienzo():
    return [["."] * 16 for _ in range(16)]


def px(g, x, y, c):
    if 0 <= x < 16 and 0 <= y < 16:
        g[y][x] = c


def rect(g, x0, y0, x1, y1, c):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            px(g, x, y, c)


def borde(g, x0, y0, x1, y1, c):
    rect(g, x0, y0, x1, y1, "0")
    rect(g, x0 + 1, y0 + 1, x1 - 1, y1 - 1, c)


def espejo(g):
    return [f[::-1] for f in g]


def texto(g):
    return ["".join(f) for f in g]


def piernas(g, a_izq, a_der):
    for x, alto in ((6, a_izq), (8, a_der)):
        rect(g, x, 11, x + 1, 10 + alto, "1")
        rect(g, x, 11 + alto, x + 1, 11 + alto, "0")


def guardiana(direccion, frame, brazos_arriba=False):
    g = lienzo()
    lado = direccion in ("derecha", "izquierda")
    if lado:
        borde(g, 6, 4, 11, 6, "3")
        px(g, 10, 5, "0")
    else:
        borde(g, 5, 4, 10, 6, "3" if direccion == "abajo" else "1")
        if direccion == "abajo":
            px(g, 6, 5, "0")
            px(g, 9, 5, "0")
    borde(g, 5, 1, 10, 3, "2")
    rect(g, 3, 3, 12, 3, "1")
    borde(g, 5, 7, 10, 10, "7")
    if brazos_arriba:
        rect(g, 3, 5, 4, 8, "3")
        rect(g, 11, 5, 12, 8, "3")
        px(g, 2, 3, "e")
        px(g, 13, 3, "e")
        px(g, 13, 2, "f")
    elif lado:
        rect(g, 7, 8, 8, 10, "3")
    else:
        rect(g, 3, 8, 4, 10, "3")
        rect(g, 11, 8, 12, 10, "3")
    altos = {0: (3, 3), 1: (2, 3), 2: (3, 2)}[frame]
    piernas(g, *altos)
    return espejo(g) if direccion == "izquierda" else g


def loro():
    g = lienzo()
    borde(g, 4, 5, 9, 11, "7")
    borde(g, 5, 2, 9, 5, "7")
    rect(g, 8, 3, 9, 4, "c")
    rect(g, 10, 3, 11, 4, "b")
    px(g, 8, 3, "0")
    rect(g, 4, 7, 7, 10, "6")
    rect(g, 4, 12, 6, 14, "a")
    rect(g, 6, 12, 8, 13, "c")
    return g, (8, 3)


def zorro():
    g = lienzo()
    borde(g, 0, 5, 3, 8, "3")
    rect(g, 0, 5, 1, 6, "5")
    borde(g, 3, 6, 11, 10, "2")
    rect(g, 4, 9, 10, 9, "4")
    borde(g, 10, 3, 14, 7, "2")
    px(g, 10, 2, "0")
    px(g, 12, 2, "0")
    rect(g, 13, 5, 14, 6, "4")
    px(g, 14, 5, "0")
    px(g, 12, 4, "0")
    for x in (4, 6, 8, 10):
        rect(g, x, 11, x, 13, "1")
    return g, (12, 4)


def oso():
    g = lienzo()
    borde(g, 0, 5, 3, 10, "2")
    borde(g, 3, 6, 11, 11, "1")
    rect(g, 5, 8, 9, 8, "5")
    borde(g, 5, 3, 8, 5, "3")
    borde(g, 10, 5, 13, 9, "2")
    rect(g, 13, 7, 15, 8, "3")
    px(g, 12, 6, "0")
    rect(g, 4, 12, 5, 14, "1")
    rect(g, 9, 12, 10, 14, "1")
    return g, (12, 6)


def tatu():
    g = lienzo()
    rect(g, 0, 8, 2, 9, "2")
    borde(g, 2, 5, 11, 11, "3")
    for x in (4, 6, 8):
        rect(g, x, 6, x, 10, "2")
    borde(g, 11, 7, 14, 10, "2")
    px(g, 13, 8, "0")
    rect(g, 4, 12, 5, 14, "2")
    rect(g, 9, 12, 10, 14, "2")
    return g, (13, 8)


def tagua():
    g = lienzo()
    borde(g, 3, 5, 11, 10, "1")
    rect(g, 9, 6, 9, 9, "5")
    borde(g, 11, 6, 14, 10, "2")
    rect(g, 14, 8, 15, 9, "3")
    px(g, 12, 7, "0")
    px(g, 11, 5, "0")
    for x in (4, 6, 8, 10):
        rect(g, x, 11, x, 13, "1")
    return g, (12, 7)


def tortuga():
    g = lienzo()
    borde(g, 3, 6, 11, 11, "6")
    rect(g, 5, 7, 6, 8, "7")
    rect(g, 8, 7, 9, 8, "7")
    rect(g, 6, 9, 9, 10, "7")
    borde(g, 11, 8, 14, 10, "8")
    px(g, 13, 9, "0")
    px(g, 2, 10, "8")
    rect(g, 4, 12, 5, 13, "8")
    rect(g, 9, 12, 10, 13, "8")
    return g, (13, 9)


def estado(base, ojo, est):
    g = [f[:] for f in base]
    ox, oy = ojo
    if est == "asustado":
        px(g, ox, oy, "5")
        px(g, ox, oy + 1, "e")
        for y in (0, 1, 3):
            px(g, 2, y, "b")
    elif est == "refugiado":
        for x, y in ((1, 0), (2, 0), (3, 0), (2, 1), (1, 2), (2, 2), (3, 2)):
            px(g, x, y, "f")
    return g


def guardiana(direccion, frame, brazos_arriba=False):
    g = lienzo()
    lado = direccion in ("derecha", "izquierda")
    espalda = direccion == "arriba"
    borde(g, 5, 0, 10, 2, "2")
    if lado:
        rect(g, 4, 3, 13, 3, "1")
        borde(g, 6, 4, 11, 8, "3")
        rect(g, 7, 5, 8, 7, "1")
        px(g, 10, 6, "0")
        px(g, 11, 6, "3")
        borde(g, 6, 9, 10, 12, "7")
    else:
        rect(g, 3, 3, 12, 3, "1")
        if espalda:
            borde(g, 5, 4, 10, 8, "1")
            rect(g, 7, 5, 8, 5, "2")
        else:
            borde(g, 5, 4, 10, 8, "3")
            px(g, 6, 6, "0")
            px(g, 9, 6, "0")
            rect(g, 7, 7, 8, 7, "a")
        borde(g, 5, 9, 10, 12, "7")
    if brazos_arriba:
        rect(g, 3, 6, 4, 9, "3")
        rect(g, 11, 6, 12, 9, "3")
        px(g, 2, 4, "e")
        px(g, 13, 4, "e")
        px(g, 13, 3, "f")
    elif lado:
        rect(g, 7, 10, 8, 12, "3")
        borde(g, 4, 10, 5, 12, "2")
    else:
        rect(g, 3, 9, 4, 12, "3")
        rect(g, 11, 9, 12, 12, "3")
        if espalda:
            borde(g, 6, 10, 9, 12, "2")
    altos = {0: (3, 3), 1: (2, 3), 2: (3, 2)}[frame]
    for x, alto in ((6, altos[0]), (8, altos[1])):
        rect(g, x, 13, x + 1, 12 + alto, "1")
    return espejo(g) if direccion == "izquierda" else g


def tagua():
    g = lienzo()
    for x in (4, 6, 8, 10):
        px(g, x, 4, "0")
    borde(g, 3, 5, 11, 10, "1")
    for x, y in ((5, 7), (7, 6), (8, 8), (5, 9), (6, 8)):
        px(g, x, y, "2")
    for x, y in ((10, 6), (9, 7), (8, 8), (7, 9)):
        px(g, x, y, "5")
    for x, y in ((9, 6), (8, 7), (7, 8), (6, 9)):
        px(g, x, y, "4")
    px(g, 2, 7, "2")
    borde(g, 11, 6, 14, 10, "2")
    px(g, 12, 4, "0")
    px(g, 11, 5, "0")
    px(g, 12, 5, "2")
    px(g, 13, 5, "0")
    rect(g, 14, 8, 15, 9, "3")
    px(g, 15, 8, "0")
    px(g, 15, 10, "0")
    px(g, 12, 7, "0")
    rect(g, 4, 11, 5, 13, "1")
    rect(g, 9, 11, 10, 13, "1")
    rect(g, 4, 14, 5, 14, "0")
    rect(g, 9, 14, 10, 14, "0")
    return g, (12, 7)


S = {}
for d in ("abajo", "arriba", "derecha", "izquierda"):
    for f in range(3):
        S[f"guardiana_{d}_{f}"] = guardiana(d, f)
S["guardiana_accion"] = guardiana("abajo", 0, True)
for nombre, fn in (("loro", loro), ("zorro", zorro), ("oso", oso),
                   ("tatu", tatu), ("tagua", tagua), ("tortuga", tortuga)):
    base, ojo = fn()
    for est in ("normal", "asustado", "refugiado"):
        S[f"animal_{nombre}_{est}"] = estado(base, ojo, est)

with open("src/cliente/sprites.py", "w", encoding="utf-8") as f:
    f.write('"""Sprites 16x16 en texto. "." es transparente; el resto es un indice hex de paleta.\n')
    f.write('Generado por scripts/gen_sprites.py."""\n\nSPRITES = {\n')
    for k, g in S.items():
        f.write(f'    "{k}": [\n')
        for fila in texto(g):
            f.write(f'        "{fila}",\n')
        f.write("    ],\n")
    f.write("}\n\n")
    f.write('if __name__ == "__main__":\n')
    f.write("    from paleta import PALETA\n")
    f.write("    for nombre, filas in SPRITES.items():\n")
    f.write('        assert len(filas) == 16, f"{nombre}: {len(filas)} filas"\n')
    f.write("        for fila in filas:\n")
    f.write('            assert len(fila) == 16, f"{nombre}: fila de {len(fila)} columnas"\n')
    f.write('            assert all(c == "." or int(c, 16) < len(PALETA) for c in fila), nombre\n')
    f.write('    print(f"OK: {len(SPRITES)} sprites validos (16x16)")\n')
print(f"{len(S)} sprites escritos en src/cliente/sprites.py")
