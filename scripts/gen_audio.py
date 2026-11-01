#!/usr/bin/env python3
"""Genera efectos y musica chiptune en src/cliente/audio/ (WAV mono, 16 bits, 22050 Hz).
Solo numpy y la libreria estandar; sin archivos externos. Es determinista.
Uso: python3 scripts/gen_audio.py"""
import os
import random
import sys
import wave

import numpy as np

SR = 22050
SALIDA = "src/cliente/audio"


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def onda(tipo, fase):
    if tipo == "cuadrada":
        return np.where(fase < 0.5, 1.0, -1.0)
    if tipo == "pulso":
        return np.where(fase < 0.25, 1.0, -1.0)
    return 4.0 * np.abs(fase - 0.5) - 1.0  # triangular


def nota(f, dur, tipo="cuadrada", vol=1.0, decay=5.0, f_fin=None):
    n = max(int(SR * dur), 1)
    if f == 0:
        return np.zeros(n)
    t = np.arange(n) / SR
    frec = (f if f_fin is None else np.linspace(f, f_fin, n)) * np.ones(n)
    fase = (np.cumsum(frec) / SR) % 1.0
    env = np.minimum(1.0, t / 0.004) * np.exp(-decay * t / dur)
    env *= np.minimum(1.0, (n - 1 - np.arange(n)) / (SR * 0.006))
    return onda(tipo, fase) * env * vol


def silencio(dur):
    return np.zeros(int(SR * dur))


def unir(*partes):
    return np.concatenate(partes)


def poner(buf, inicio, senal):
    i = int(round(inicio * SR))
    if i >= len(buf):
        return
    fin = min(i + len(senal), len(buf))
    buf[i:fin] += senal[:fin - i]


def guardar(nombre, senal, pico=0.8):
    m = np.max(np.abs(senal))
    datos = (senal / m * pico * 32767).astype("<i2")
    with wave.open(os.path.join(SALIDA, nombre), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(datos.tobytes())


def efectos():
    guardar("clic.wav", nota(1500, 0.05, "cuadrada", decay=8))
    guardar("colocar.wav", unir(nota(midi(67), 0.06), nota(midi(72), 0.10)))
    gotas = []
    for f0, f1 in ((500, 900), (600, 1100), (450, 800)):
        gotas += [nota(f0, 0.12, "triangular", decay=5, f_fin=f1), silencio(0.03)]
    guardar("agua.wav", unir(*gotas))
    guardar("rescate.wav", unir(
        nota(midi(72), 0.09, "triangular"), nota(midi(76), 0.09, "triangular"),
        nota(midi(79), 0.09, "triangular"), nota(midi(84), 0.25, "triangular", decay=3)))
    sirena = []
    for _ in range(3):
        sirena += [nota(880, 0.12, "cuadrada", decay=2), nota(660, 0.12, "cuadrada", decay=2)]
    guardar("alerta_fuego.wav", unir(*sirena))
    acorde = np.zeros(int(0.5 * SR))
    for m in (84, 79, 76):
        acorde += nota(midi(m), 0.5, "pulso", 0.6, decay=2)
    guardar("victoria.wav", unir(
        nota(midi(72), 0.12, "pulso"), nota(midi(76), 0.12, "pulso"),
        nota(midi(79), 0.12, "pulso"), acorde))


def musica():
    bpm, compases = 90, 16
    comp = 4 * 60 / bpm
    corchea = comp / 8
    buf = np.zeros(int(round(compases * comp * SR)))
    escala = [0, 2, 4, 7, 9]  # pentatonica mayor
    grados = [60 + 12 * o + s for o in (0, 1) for s in escala]
    rng = random.Random(7)
    idx = 4
    for c in range(compases):
        for k in range(8):
            ultima = (c == compases - 1 and k == 7)
            if ultima:
                idx = 0
            else:
                idx = min(max(idx + rng.choice([-2, -1, -1, 0, 1, 1, 2]), 0), 9)
            if k % 2 == 1 and rng.random() < 0.15 and not ultima:
                continue
            dur = corchea
            poner(buf, c * comp + k * corchea, nota(midi(grados[idx]), dur, "pulso", 0.30, decay=3))
    raices = [48, 45, 43, 52]
    for c in range(compases):
        r = raices[c % 4]
        poner(buf, c * comp, nota(midi(r), comp / 2, "triangular", 0.6, decay=1.5))
        poner(buf, c * comp + comp / 2, nota(midi(r + 7), comp / 2, "triangular", 0.5, decay=1.5))
    guardar("musica_chaco.wav", buf, pico=0.6)


def validar():
    ok = True
    print(f"{'archivo':22s} {'dur(s)':>7s} {'pico':>6s}")
    for nombre in sorted(os.listdir(SALIDA)):
        if not nombre.endswith(".wav"):
            continue
        with wave.open(os.path.join(SALIDA, nombre), "rb") as w:
            canales, ancho, tasa, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
            x = np.frombuffer(w.readframes(n), dtype="<i2").astype(int)
        dur, pico = n / tasa, int(np.max(np.abs(x)))
        if nombre.startswith("musica"):
            rango = (30.0, 60.0)
            extremos = abs(x[0]) < 600 and abs(x[-1]) < 600
        else:
            rango = (0.03, 2.0)
            extremos = True
        bien = (canales == 1 and ancho == 2 and tasa == SR and rango[0] <= dur <= rango[1]
                and 2000 < pico < 30000 and extremos)
        print(f"{nombre:22s} {dur:7.2f} {pico:6d} {'OK' if bien else 'FALLA'}")
        ok &= bool(bien)
    return ok


if __name__ == "__main__":
    os.makedirs(SALIDA, exist_ok=True)
    efectos()
    musica()
    if validar():
        print("OK: audio generado y validado en", SALIDA)
    else:
        print("ERROR: algun archivo no paso la validacion")
        sys.exit(1)
