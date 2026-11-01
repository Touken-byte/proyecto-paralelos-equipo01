#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "vigia.h"

void vigia_simular(Mapa *m, ParamsFuego p, int pasos, int k_ini, int k_fin, uint32_t *cuenta) {
    size_t n = (size_t)m->ancho * (size_t)m->alto;
    uint8_t *ini = malloc(n);
    if (!ini) return;
    memcpy(ini, m->actual, n);
    uint64_t seed0 = p.seed;
    for (int k = k_ini; k < k_fin; k++) {
        memcpy(m->actual, ini, n);
        p.seed = seed0 + 1000003ULL * (uint64_t)(k + 1);
        for (int t = 0; t < pasos; t++) fuego_paso(m, &p, (uint64_t)t);
        for (size_t i = 0; i < n; i++)
            if (m->actual[i] == E_CENIZA || m->actual[i] == E_ARDIENDO) cuenta[i]++;
    }
    free(ini);
}

uint64_t vigia_hash(const uint32_t *c, size_t n) {
    uint64_t h = 1469598103934665603ULL;
    for (size_t i = 0; i < n; i++) {
        uint32_t v = c[i];
        for (int b = 0; b < 4; b++) { h ^= (v >> (8 * b)) & 0xFFu; h *= 1099511628211ULL; }
    }
    return h;
}

int vigia_ppm(const uint32_t *c, int N, int nsims, const char *ruta, int escala) {
    FILE *f = fopen(ruta, "wb");
    if (!f) return -1;
    fprintf(f, "P6\n%d %d\n255\n", N * escala, N * escala);
    for (int y = 0; y < N * escala; y++)
        for (int x = 0; x < N * escala; x++) {
            double pr = (double)c[(size_t)(y / escala) * N + (x / escala)] / (double)nsims;
            fputc((int)(20 + 235 * pr), f);
            fputc((int)(40 + 50 * pr), f);
            fputc((int)(20 - 20 * pr), f);
        }
    fclose(f);
    return 0;
}
