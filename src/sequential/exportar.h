#ifndef EXPORTAR_H
#define EXPORTAR_H

#include "mapa.h"

/* Escribe el estado actual como imagen PGM (P5), ampliada por "escala".
   Devuelve 0 si salio bien. */
int exportar_pgm(const Mapa *m, const char *ruta, int escala);

#endif
