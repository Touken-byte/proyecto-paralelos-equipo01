#ifndef FUEGO_H
#define FUEGO_H

#include <stdint.h>
#include "mapa.h"

typedef struct {
    double p_base;         /* probabilidad base de contagio */
    double viento_x;       /* direccion hacia donde sopla */
    double viento_y;
    double viento_fuerza;  /* 0 = sin efecto */
    double k_pendiente;    /* sensibilidad a la pendiente */
    uint64_t seed;
} ParamsFuego;

ParamsFuego fuego_params_default(uint64_t seed);

/* Lee m->actual, escribe m->siguiente y luego intercambia los buffers */
void fuego_paso(Mapa *m, const ParamsFuego *p, uint64_t paso);

#endif
