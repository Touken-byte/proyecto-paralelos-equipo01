"""Tiles de 16x16 definidos como texto. Cada caracter es un indice de paleta (hex)."""

TILES = {
    "pasto": [
        "8888888988888898",
        "8898888888988888",
        "8888988888888988",
        "9888888898888888",
        "8888898888898888",
        "8988888888888998",
        "8888888988888888",
        "8898888888988888",
        "8888888888888898",
        "9888898888888888",
        "8888888898888988",
        "8898888888898888",
        "8888988888888888",
        "8888888889888898",
        "8988888888888888",
        "8888898888988888",
    ],
    "monte": [
        "7777677777767777",
        "7767777777777677",
        "7777777677777777",
        "6777777777767777",
        "7777767777777776",
        "7677777777677777",
        "7777777767777677",
        "7777677777777777",
        "7767777777776777",
        "7777777677777767",
        "6777777777767777",
        "7777767777777777",
        "7777777777677777",
        "7677777767777677",
        "7777776777777777",
        "7767777777776777",
    ],
    "agua": [
        "dddddddddddddddd",
        "ddeedddddddeeddd",
        "dddddddddddddddd",
        "dddddeedddddddff",
        "dddddddddddddddd",
        "eeddddddddeedddd",
        "dddddddddddddddd",
        "ddddddddeedddddd",
        "dddddddddddddddd",
        "ddeeddddddddeedd",
        "dddddddddddddddd",
        "dddddddddddeeddd",
        "eeddddddddddddff",
        "dddddddddddddddd",
        "dddeedddddddeedd",
        "dddddddddddddddd",
    ],
    "fuego": [
        "1111111b11111111",
        "111111bbb1111111",
        "11111bbcbb111111",
        "1111bbcccbb11111",
        "111bbbcccbbb1111",
        "11bbbccccbbbb111",
        "11bbcccccccbb111",
        "1bbbcccfcccbbb11",
        "1bbccccccccbbb11",
        "1bbcccccccccbb11",
        "1bbbccccccccbb11",
        "11bbbcccccbbb111",
        "11abbbcccbbba111",
        "111aabbbbbaa1111",
        "1111aaaaaaa11111",
        "1111111aa1111111",
    ],
}

if __name__ == "__main__":
    from paleta import PALETA
    for nombre, filas in TILES.items():
        assert len(filas) == 16, f"{nombre}: {len(filas)} filas"
        for f in filas:
            assert len(f) == 16, f"{nombre}: fila de {len(f)} columnas"
            assert all(ch in "0123456789abcdef" for ch in f), f"{nombre}: caracter invalido"
            assert all(int(ch, 16) < len(PALETA) for ch in f)
        print(f"{nombre}: 16x16 OK")
    print("OK: tiles validos")
