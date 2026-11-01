#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include "mapgen.h"
#include "exportar.h"

static uint64_t checksum(const Mapa *m) {
    uint64_t h = 1469598103934665603ULL;
    size_t n = (size_t)m->ancho * (size_t)m->alto;
    for (size_t i = 0; i < n; i++) { h ^= m->actual[i]; h *= 1099511628211ULL; }
    return h;
}

/* uso: secuencial NIVEL SEED PASOS [salida.pgm] */
int main(int argc, char **argv) {
    if (argc != 4 && argc != 5) {
        fprintf(stderr, "uso: %s NIVEL SEED PASOS [salida.pgm]\n", argv[0]);
        return 2;
    }
    int nivel = atoi(argv[1]);
    uint64_t seed = strtoull(argv[2], NULL, 10);
    int pasos = atoi(argv[3]);
    Mapa *m = mapgen_nivel(nivel, seed);
    if (!m) { fprintf(stderr, "nivel invalido\n"); return 1; }
    ParamsFuego p = mapgen_params(nivel, seed);
    for (int t = 0; t < pasos; t++) fuego_paso(m, &p, (uint64_t)t);
    long q = mapa_contar(m, E_CENIZA) + mapa_contar(m, E_ARDIENDO);
    printf("hash=%016llx quemadas=%ld\n", (unsigned long long)checksum(m), q);
    if (argc == 5 && exportar_pgm(m, argv[4], 4) != 0) {
        fprintf(stderr, "no se pudo escribir %s\n", argv[4]);
        mapa_liberar(m);
        return 1;
    }
    mapa_liberar(m);
    return 0;
}
