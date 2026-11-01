#include <math.h>
#include "fuego_mpi.h"
#include "mapa.h"
#include "rng.h"

#define RAIZ2 1.41421356237309504880

static double combustible(uint8_t t) {
    switch (t) {
        case T_PASTO:        return 0.8;
        case T_MONTE_SECO:   return 1.0;
        case T_MONTE_DENSO:  return 0.6;
        case T_RIBERA:       return 0.1;
        default:             return 0.0;
    }
}

void fuego_paso_bloque(const uint8_t *act, uint8_t *sig,
                       const uint8_t *terr, const uint8_t *hum, const uint8_t *rel,
                       int W, int filas, int y0,
                       const ParamsFuego *p, uint64_t paso) {
    const double vn = sqrt(p->viento_x * p->viento_x + p->viento_y * p->viento_y);
    const double ux = vn > 0.0 ? p->viento_x / vn : 0.0;
    const double uy = vn > 0.0 ? p->viento_y / vn : 0.0;

#ifdef _OPENMP
    #pragma omp parallel for schedule(static)
#endif
    for (int y = 1; y <= filas; y++) {
        for (int x = 0; x < W; x++) {
            size_t i = (size_t)y * W + x;
            uint64_t global = (uint64_t)(y0 + y - 1) * (uint64_t)W + (uint64_t)x;
            uint8_t e = act[i];

            if (e == E_ARDIENDO) { sig[i] = E_CENIZA; continue; }
            if (e == E_CENIZA)   { sig[i] = E_CENIZA; continue; }

            double c = combustible(terr[i]);
            if (c <= 0.0) { sig[i] = E_SIN_QUEMAR; continue; }

            double h = hum[i] / 255.0;
            double no_enciende = 1.0;

            for (int dy = -1; dy <= 1; dy++) {
                for (int dx = -1; dx <= 1; dx++) {
                    if (dx == 0 && dy == 0) continue;
                    int nx = x + dx, ny = y + dy;
                    if (nx < 0 || nx >= W) continue;
                    size_t j = (size_t)ny * W + nx;
                    if (act[j] != E_ARDIENDO) continue;

                    int diag = (dx != 0 && dy != 0);
                    double d = diag ? RAIZ2 : 1.0;
                    double cosang = ((-dx) * ux + (-dy) * uy) / d;
                    double fv = 1.0 + p->viento_fuerza * cosang;
                    if (fv < 0.0) fv = 0.0;
                    double subida = ((double)rel[i] - (double)rel[j]) / 255.0 / d;
                    double fp = exp(p->k_pendiente * subida);
                    double fd = diag ? 1.0 / RAIZ2 : 1.0;

                    double pn = p->p_base * c * (1.0 - h) * fv * fp * fd;
                    if (pn < 0.0) pn = 0.0;
                    if (pn > 1.0) pn = 1.0;
                    no_enciende *= (1.0 - pn);
                }
            }

            double pig = 1.0 - no_enciende;
            if (pig > 0.0 && rng_uniforme(p->seed, paso, global) < pig)
                sig[i] = E_ARDIENDO;
            else
                sig[i] = E_SIN_QUEMAR;
        }
    }
}
