"""Audio del cliente (S7-L5): efectos y musica con pygame.mixer.
Si no hay dispositivo de sonido o faltan los WAV, el juego sigue en silencio."""
import os

import pygame

EFECTOS = ["clic", "colocar", "agua", "rescate", "alerta_fuego", "victoria"]
AQUI = os.path.dirname(os.path.abspath(__file__))


class Sonido:
    def __init__(self):
        self.ok, self.silencio = False, False
        self.efectos, self.musica, self.vol_musica = {}, None, 0.3

    def activar(self, carpeta=None):
        carpeta = carpeta or os.path.join(AQUI, "audio")
        try:
            pygame.mixer.init()
            self.efectos = {n: pygame.mixer.Sound(os.path.join(carpeta, n + ".wav")) for n in EFECTOS}
            self.musica = pygame.mixer.Sound(os.path.join(carpeta, "musica_chaco.wav"))
            self.musica.set_volume(self.vol_musica)
            self.musica.play(loops=-1)
            self.ok = True
        except Exception as ex:
            self.ok, self.efectos, self.musica = False, {}, None
            print("audio desactivado:", ex)
        return self.ok

    def play(self, nombre):
        if self.ok and not self.silencio and nombre in self.efectos:
            self.efectos[nombre].play()

    def alternar(self):
        self.silencio = not self.silencio
        if self.ok and self.musica:
            self.musica.set_volume(0.0 if self.silencio else self.vol_musica)
        return self.silencio
