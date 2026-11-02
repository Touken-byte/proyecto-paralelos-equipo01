#include <stdio.h>
#include <stdint.h>
#include "mapgen.h"

static uint64_t checksum(const Mapa *m) {
    uint64_t h = 1469598103934665603ULL;
    size_t n = (size_t)m->ancho * (size_t)m->alto;
    for (size_t i = 0; i < n; i++) {
        h ^= m->terreno[i]; h *= 1099511628211ULL;
        h ^= m->humedad[i]; h *= 1099511628211ULL;
        h ^= m->relieve[i]; h *= 1099511628211ULL;
    }
    return h;
}

int main(void) {
    int ok = 1;
    for (int nivel = 1; nivel <= 3; nivel++) {
        Mapa *a = mapgen_nivel(nivel, 42);
        Mapa *b = mapgen_nivel(nivel, 42);
        Mapa *c = mapgen_nivel(nivel, 43);
        uint64_t ha = checksum(a), hb = checksum(b), hc = checksum(c);
        long cnt[7] = {0};
        size_t n = (size_t)a->ancho * (size_t)a->alto;
        for (size_t i = 0; i < n; i++) cnt[a->terreno[i]]++;

        printf("nivel %d (%dx%d): seed42=%016llx seed42=%016llx seed43=%016llx\n",
               nivel, a->ancho, a->alto, (unsigned long long)ha,
               (unsigned long long)hb, (unsigned long long)hc);
        printf("  pasto=%ld seco=%ld denso=%ld ribera=%ld agua=%ld focos=%ld\n",
               cnt[T_PASTO], cnt[T_MONTE_SECO], cnt[T_MONTE_DENSO],
               cnt[T_RIBERA], cnt[T_AGUA], mapa_contar(a, E_ARDIENDO));

        ParamsFuego p = mapgen_params(nivel, 42);
        for (int t = 0; t < 40; t++) fuego_paso(a, &p, (uint64_t)t);
        long q = mapa_contar(a, E_CENIZA) + mapa_contar(a, E_ARDIENDO);
        printf("  tras 40 pasos: quemadas=%ld\n", q);

        if (ha != hb || ha == hc || q <= 1) ok = 0;
        mapa_liberar(a); mapa_liberar(b); mapa_liberar(c);
    }
    printf(ok ? "RESULTADO: OK\n" : "RESULTADO: FALLO\n");
    return ok ? 0 : 1;
}
