#ifndef FUEGO_MPI_H
#define FUEGO_MPI_H

#include <stdint.h>
#include "fuego.h"

/* Paso del automata sobre un bloque de "filas" filas del mapa.
   Los arreglos tienen (filas+2) filas: la 0 y la filas+1 son fantasma.
   y0 = fila global de la primera fila real. Filas fantasma fuera del mapa
   deben estar en cero. */
void fuego_paso_bloque(const uint8_t *act, uint8_t *sig,
                       const uint8_t *terr, const uint8_t *hum, const uint8_t *rel,
                       int W, int filas, int y0,
                       const ParamsFuego *p, uint64_t paso);

#endif
