#include <stdio.h>
#include "mapa.h"

int main(void) {
    Mapa *m = mapa_crear(64, 64);
    if (!m) { fprintf(stderr, "sin memoria\n"); return 1; }

    m->actual[mapa_idx(m, 10, 10)] = E_ARDIENDO;
    m->siguiente[mapa_idx(m, 10, 10)] = E_CENIZA;

    printf("antes:   ardiendo=%ld ceniza=%ld\n",
           mapa_contar(m, E_ARDIENDO), mapa_contar(m, E_CENIZA));
    mapa_intercambiar(m);
    printf("despues: ardiendo=%ld ceniza=%ld\n",
           mapa_contar(m, E_ARDIENDO), mapa_contar(m, E_CENIZA));

    mapa_liberar(m);
    return 0;
}
