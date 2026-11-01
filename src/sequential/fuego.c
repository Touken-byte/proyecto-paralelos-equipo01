#include <math.h>
#include "fuego.h"
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

ParamsFuego fuego_params_default(uint64_t seed) {
    ParamsFuego p;
    p.p_base = 0.5;
    p.viento_x = 0.0;
    p.viento_y = 0.0;
    p.viento_fuerza = 0.8;
    p.k_pendiente = 2.0;
    p.seed = seed;
    return p;
}

void fuego_paso(Mapa *m, const ParamsFuego *p, uint64_t paso) {
    const int W = m->ancho, H = m->alto;
    double vn = sqrt(p->viento_x * p->viento_x + p->viento_y * p->viento_y);
    double ux = vn > 0.0 ? p->viento_x / vn : 0.0;
    double uy = vn > 0.0 ? p->viento_y / vn : 0.0;

    for (int y = 0; y < H; y++) {
        for (int x = 0; x < W; x++) {
            size_t i = mapa_idx(m, x, y);
            uint8_t e = m->actual[i];

            if (e == E_ARDIENDO) { m->siguiente[i] = E_CENIZA; continue; }
            if (e == E_CENIZA)   { m->siguiente[i] = E_CENIZA; continue; }

            double c = combustible(m->terreno[i]);
            if (c <= 0.0) { m->siguiente[i] = E_SIN_QUEMAR; continue; }

            double h = m->humedad[i] / 255.0;
            double no_enciende = 1.0;

            for (int dy = -1; dy <= 1; dy++) {
                for (int dx = -1; dx <= 1; dx++) {
                    if (dx == 0 && dy == 0) continue;
                    int nx = x + dx, ny = y + dy;
                    if (nx < 0 || ny < 0 || nx >= W || ny >= H) continue;
                    size_t j = mapa_idx(m, nx, ny);
                    if (m->actual[j] != E_ARDIENDO) continue;

                    int diag = (dx != 0 && dy != 0);
                    double d = diag ? RAIZ2 : 1.0;
                    /* direccion del vecino hacia esta celda = (-dx,-dy) */
                    double cosang = ((-dx) * ux + (-dy) * uy) / d;
                    double fv = 1.0 + p->viento_fuerza * cosang;
                    if (fv < 0.0) fv = 0.0;
                    double subida = ((double)m->relieve[i] - (double)m->relieve[j]) / 255.0 / d;
                    double fp = exp(p->k_pendiente * subida);
                    double fd = diag ? 1.0 / RAIZ2 : 1.0;

                    double pn = p->p_base * c * (1.0 - h) * fv * fp * fd;
                    if (pn < 0.0) pn = 0.0;
                    if (pn > 1.0) pn = 1.0;
                    no_enciende *= (1.0 - pn);
                }
            }

            double pig = 1.0 - no_enciende;
            if (pig > 0.0 && rng_uniforme(p->seed, paso, (uint64_t)i) < pig)
                m->siguiente[i] = E_ARDIENDO;
            else
                m->siguiente[i] = E_SIN_QUEMAR;
        }
    }
    mapa_intercambiar(m);
}
