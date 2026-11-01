#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "mapgen.h"
#include "vigia.h"

static double ahora(void) {
    struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

/* uso: bench_vigia N SEED PASOS NSIMS [salida.ppm] -> tiempo_s,hash,suma_conteos */
int main(int argc, char **argv) {
    if (argc < 5) { fprintf(stderr, "uso: %s N SEED PASOS NSIMS [salida.ppm]\n", argv[0]); return 2; }
    int N = atoi(argv[1]);
    uint64_t seed = strtoull(argv[2], NULL, 10);
    int pasos = atoi(argv[3]), nsims = atoi(argv[4]);
    Mapa *m = mapgen_tamano(N, seed);
    if (!m) { fprintf(stderr, "N invalido o sin memoria\n"); return 1; }
    ParamsFuego p = mapgen_params(2, seed);
    size_t n = (size_t)N * N;
    uint32_t *c = calloc(n, sizeof(uint32_t));
    double t0 = ahora();
    vigia_simular(m, p, pasos, 0, nsims, c);
    double t1 = ahora();
    unsigned long long suma = 0;
    for (size_t i = 0; i < n; i++) suma += c[i];
    printf("%.4f,%016llx,%llu\n", t1 - t0, (unsigned long long)vigia_hash(c, n), suma);
    if (argc > 5) vigia_ppm(c, N, nsims, argv[5], 4);
    free(c); mapa_liberar(m);
    return 0;
}
