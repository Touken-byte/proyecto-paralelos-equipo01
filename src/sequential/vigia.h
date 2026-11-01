#ifndef VIGIA_H
#define VIGIA_H

#include <stdint.h>
#include <stddef.h>
#include "mapa.h"
#include "fuego.h"

/* Simula las corridas k_ini..k_fin-1 sobre el mapa m (estado inicial = m->actual).
   Suma en cuenta[celda] las veces que la celda terminó quemada. */
void vigia_simular(Mapa *m, ParamsFuego p, int pasos, int k_ini, int k_fin, uint32_t *cuenta);
uint64_t vigia_hash(const uint32_t *c, size_t n);
/* Mapa de probabilidad a color (PPM), escalado "escala" veces */
int vigia_ppm(const uint32_t *c, int N, int nsims, const char *ruta, int escala);

#endif
