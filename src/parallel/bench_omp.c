#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <omp.h>
#include "mapgen.h"
#include "fuego_omp.h"

static uint64_t checksum(const Mapa *m) {
    uint64_t h = 1469598103934665603ULL;
    size_t n = (size_t)m->ancho * (size_t)m->alto;
    for (size_t i = 0; i < n; i++) { h ^= m->actual[i]; h *= 1099511628211ULL; }
    return h;
}

static double ahora(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

/* uso: OMP_NUM_THREADS=k bench_omp N SEED PASOS -> tiempo_s,hash,quemadas */
int main(int argc, char **argv) {
    if (argc != 4) { fprintf(stderr, "uso: %s N SEED PASOS\n", argv[0]); return 2; }
    int N = atoi(argv[1]);
    uint64_t seed = strtoull(argv[2], NULL, 10);
    int pasos = atoi(argv[3]);
    Mapa *m = mapgen_tamano(N, seed);
    if (!m) { fprintf(stderr, "N invalido o sin memoria\n"); return 1; }
    ParamsFuego p = mapgen_params(2, seed);

    double t0 = ahora();
    for (int t = 0; t < pasos; t++) fuego_paso_omp(m, &p, (uint64_t)t);
    double t1 = ahora();

    long q = mapa_contar(m, E_CENIZA) + mapa_contar(m, E_ARDIENDO);
    fprintf(stderr, "hilos=%d\n", omp_get_max_threads());
    printf("%.4f,%016llx,%ld\n", t1 - t0, (unsigned long long)checksum(m), q);
    mapa_liberar(m);
    return 0;
}
