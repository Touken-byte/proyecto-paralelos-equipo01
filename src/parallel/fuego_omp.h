#ifndef FUEGO_OMP_H
#define FUEGO_OMP_H

#include <stdint.h>
#include "mapa.h"
#include "fuego.h"

/* Igual que fuego_paso, pero con OpenMP sobre las filas. */
void fuego_paso_omp(Mapa *m, const ParamsFuego *p, uint64_t paso);

long mapa_contar_omp(const Mapa *m, uint8_t estado);

#endif
