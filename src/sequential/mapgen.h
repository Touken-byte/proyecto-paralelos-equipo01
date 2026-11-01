#ifndef MAPGEN_H
#define MAPGEN_H

#include <stdint.h>
#include "mapa.h"
#include "fuego.h"

/* nivel 1: 64x64, sin viento. nivel 2: 128x128, viento del sur, rio y relieve.
   Devuelve NULL si el nivel no existe. */
Mapa *mapgen_nivel(int nivel, uint64_t seed);
ParamsFuego mapgen_params(int nivel, uint64_t seed);

#endif
