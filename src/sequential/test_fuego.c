#include <stdio.h>
#include <stdint.h>
#include "mapa.h"
#include "fuego.h"

static uint64_t checksum(const Mapa *m) {
    uint64_t h = 1469598103934665603ULL;
    size_t n = (size_t)m->ancho * (size_t)m->alto;
    for (size_t i = 0; i < n; i++) { h ^= m->actual[i]; h *= 1099511628211ULL; }
    return h;
}

static uint64_t correr(uint64_t seed, int pasos, long *quemadas) {
    Mapa *m = mapa_crear(64, 64);
    size_t n = 64 * 64;
    for (size_t i = 0; i < n; i++) { m->terreno[i] = T_PASTO; m->humedad[i] = 60; }
    m->actual[mapa_idx(m, 32, 32)] = E_ARDIENDO;
    ParamsFuego p = fuego_params_default(seed);
    p.viento_x = 1.0;
    for (int t = 0; t < pasos; t++) fuego_paso(m, &p, (uint64_t)t);
    *quemadas = mapa_contar(m, E_CENIZA) + mapa_contar(m, E_ARDIENDO);
    uint64_t h = checksum(m);
    mapa_liberar(m);
    return h;
}

int main(void) {
    long q1, q2, q3;
    uint64_t h1 = correr(42, 60, &q1);
    uint64_t h2 = correr(42, 60, &q2);
    uint64_t h3 = correr(43, 60, &q3);
    printf("seed 42 (1): hash=%016llx quemadas=%ld\n", (unsigned long long)h1, q1);
    printf("seed 42 (2): hash=%016llx quemadas=%ld\n", (unsigned long long)h2, q2);
    printf("seed 43    : hash=%016llx quemadas=%ld\n", (unsigned long long)h3, q3);
    int ok = (h1 == h2) && (h1 != h3) && (q1 > 1);
    printf(ok ? "RESULTADO: OK\n" : "RESULTADO: FALLO\n");
    return ok ? 0 : 1;
}
