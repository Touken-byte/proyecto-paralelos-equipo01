#include <math.h>
#include "mapgen.h"
#include "rng.h"

#define CELDA 8

static double lat(uint64_t seed, uint64_t canal, int xi, int yi) {
    return rng_uniforme(seed, canal, (uint64_t)yi * 4096u + (uint64_t)xi);
}

/* Ruido de valores suavizado: determinista por (seed, canal, x, y) */
static double ruido(uint64_t seed, uint64_t canal, int x, int y) {
    double gx = (double)x / CELDA, gy = (double)y / CELDA;
    int x0 = (int)gx, y0 = (int)gy;
    double fx = gx - x0, fy = gy - y0;
    fx = fx * fx * (3.0 - 2.0 * fx);
    fy = fy * fy * (3.0 - 2.0 * fy);
    double a = lat(seed, canal, x0, y0),     b = lat(seed, canal, x0 + 1, y0);
    double c = lat(seed, canal, x0, y0 + 1), d = lat(seed, canal, x0 + 1, y0 + 1);
    double top = a + (b - a) * fx, bot = c + (d - c) * fx;
    return top + (bot - top) * fy;
}

Mapa *mapgen_nivel(int nivel, uint64_t seed) {
    int W, H;
    if (nivel == 1) { W = 64; H = 64; }
    else if (nivel == 2) { W = 128; H = 128; }
    else if (nivel == 3) { W = 200; H = 200; }
    else return NULL;

    Mapa *m = mapa_crear(W, H);
    if (!m) return NULL;

    for (int y = 0; y < H; y++) {
        for (int x = 0; x < W; x++) {
            size_t i = mapa_idx(m, x, y);
            double v = ruido(seed, 1, x, y);
            double hum = ruido(seed, 2, x, y);
            double rel = ruido(seed, 3, x, y);

            m->terreno[i] = v < 0.30 ? T_PASTO : (v < 0.65 ? T_MONTE_SECO : T_MONTE_DENSO);
            m->humedad[i] = (uint8_t)(nivel == 1 ? 50 + hum * 40 : (nivel == 3 ? 10 + hum * 80 : 60 + hum * 80));
            m->relieve[i] = (uint8_t)(nivel == 2 ? rel * 255.0 : 128);

            if (nivel == 2) {
                double cx = W * 0.7 + 10.0 * sin(y * 0.08);
                double dist = fabs(x - cx);
                if (dist <= 2.0)      { m->terreno[i] = T_AGUA;   m->humedad[i] = 255; }
                else if (dist <= 4.0) { m->terreno[i] = T_RIBERA; m->humedad[i] = 200; }
            }
            if (nivel == 3) {
                /* Rio sinuoso vertical con un vado ancho (agua -> ribera) */
                double cx = W * 0.5 + 12.0 * sin(y * 0.05);
                double dist = fabs(x - cx);
                int vado = y >= 94 && y <= 106;
                if (dist <= 2.0)      { m->terreno[i] = vado ? T_RIBERA : T_AGUA; m->humedad[i] = vado ? 200 : 255; }
                else if (dist <= 4.0) { m->terreno[i] = T_RIBERA; m->humedad[i] = 200; }
            }
        }
    }

    int fx = nivel == 1 ? W / 2 : W / 3;
    int fy = nivel == 1 ? H / 2 : (H * 3) / 4;
    if (nivel == 3) {
        static const int PZ[4][2] = {{35, 40}, {150, 100}, {70, 110}, {150, 170}};
        for (int k = 0; k < 4; k++) {
            size_t q = mapa_idx(m, PZ[k][0], PZ[k][1]);
            m->terreno[q] = T_POZO;
            m->humedad[q] = 255;
        }
        static const int FC[3][2] = {{58, 84}, {45, 118}, {30, 60}};
        for (int j = 0; j < 3; j++)
            for (int dy = -1; dy <= 1; dy++)
                for (int dx = -1; dx <= 1; dx++) {
                    size_t q = mapa_idx(m, FC[j][0] + dx, FC[j][1] + dy);
                    m->terreno[q] = T_MONTE_SECO;
                    m->actual[q] = E_ARDIENDO;
                }
        fx = FC[0][0]; fy = FC[0][1];
    }
    size_t f = mapa_idx(m, fx, fy);
    m->terreno[f] = T_MONTE_SECO;
    m->actual[f] = E_ARDIENDO;
    return m;
}

ParamsFuego mapgen_params(int nivel, uint64_t seed) {
    ParamsFuego p = fuego_params_default(seed);
    if (nivel == 2) {
        p.viento_x = 0.0;
        p.viento_y = -1.0;   /* hacia el norte (y decrece): viento del sur */
        p.viento_fuerza = 0.8;
    } else if (nivel == 3) {
        p.viento_x = 1.0;    /* hacia el este: empuja el fuego hacia el rio */
        p.viento_y = 0.0;
        p.viento_fuerza = 0.5;
    } else {
        p.viento_fuerza = 0.0;
    }
    return p;
}

Mapa *mapgen_tamano(int N, uint64_t seed) {
    if (N < 16 || N > 8192) return NULL;
    Mapa *m = mapa_crear(N, N);
    if (!m) return NULL;

    for (int y = 0; y < N; y++) {
        for (int x = 0; x < N; x++) {
            size_t i = mapa_idx(m, x, y);
            double v = ruido(seed, 1, x, y);
            double hum = ruido(seed, 2, x, y);
            double rel = ruido(seed, 3, x, y);

            m->terreno[i] = v < 0.30 ? T_PASTO : (v < 0.65 ? T_MONTE_SECO : T_MONTE_DENSO);
            m->humedad[i] = (uint8_t)(60 + hum * 80);
            m->relieve[i] = (uint8_t)(rel * 255.0);

            double cx = N * 0.7 + 10.0 * sin(y * 0.08);
            double dist = fabs(x - cx);
            if (dist <= 2.0)      { m->terreno[i] = T_AGUA;   m->humedad[i] = 255; }
            else if (dist <= 4.0) { m->terreno[i] = T_RIBERA; m->humedad[i] = 200; }
        }
    }

    size_t f = mapa_idx(m, N / 3, (N * 3) / 4);
    m->terreno[f] = T_MONTE_SECO;
    m->actual[f] = E_ARDIENDO;
    return m;
}
