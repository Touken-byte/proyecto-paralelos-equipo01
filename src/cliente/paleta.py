"""Paleta fija de 16 colores de Guardianes del Chaco.
El indice (0-15) se escribe en los sprites como un caracter hexadecimal."""

PALETA = [
    (20, 14, 18),     # 0 negro calido (contornos)
    (74, 52, 40),     # 1 tierra oscura
    (128, 90, 58),    # 2 tierra
    (196, 160, 104),  # 3 arena
    (232, 214, 160),  # 4 crema
    (252, 250, 240),  # 5 blanco calido
    (28, 74, 44),     # 6 verde monte denso
    (52, 120, 60),    # 7 verde monte
    (112, 168, 72),   # 8 verde pasto
    (176, 204, 96),   # 9 verde claro
    (140, 40, 30),    # a rojo ceniza/brasa
    (220, 80, 30),    # b naranja fuego
    (252, 176, 48),   # c amarillo fuego
    (36, 92, 148),    # d azul agua profunda
    (72, 152, 208),   # e azul agua
    (150, 196, 224),  # f celeste
]

if __name__ == "__main__":
    assert len(PALETA) == 16
    for i, c in enumerate(PALETA):
        print(f"{i:x}: {c}")
    print("OK: 16 colores")
