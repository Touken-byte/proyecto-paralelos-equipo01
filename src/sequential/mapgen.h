#ifndef MAPGEN_H
#define MAPGEN_H

#include <stdint.h>
#include "mapa.h"
#include "fuego.h"

Mapa *mapgen_nivel(int nivel, uint64_t seed);
ParamsFuego mapgen_params(int nivel, uint64_t seed);

/* Mapa cuadrado NxN estilo nivel 2 (relieve, rio, viento del sur), para benchmark.
   N entre 16 y 8192. Devuelve NULL si N es invalido. */
Mapa *mapgen_tamano(int N, uint64_t seed);

#endif
