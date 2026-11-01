#include <stdio.h>
#include "exportar.h"

static unsigned char tono(const Mapa *m, size_t i) {
    uint8_t e = m->actual[i];
    if (e == E_ARDIENDO) return 255;
    if (e == E_CENIZA)   return 90;
    switch (m->terreno[i]) {
        case T_AGUA:       return 20;
        case T_RIBERA:     return 50;
        case T_CORTAFUEGO: return 30;
        case T_POZO:       return 20;
        case T_MONTE_DENSO:return 150;
        case T_MONTE_SECO: return 190;
        default:           return 220;
    }
}

int exportar_pgm(const Mapa *m, const char *ruta, int escala) {
    FILE *f = fopen(ruta, "wb");
    if (!f) return 1;
    fprintf(f, "P5\n%d %d\n255\n", m->ancho * escala, m->alto * escala);
    for (int y = 0; y < m->alto; y++) {
        for (int ry = 0; ry < escala; ry++) {
            for (int x = 0; x < m->ancho; x++) {
                unsigned char t = tono(m, mapa_idx(m, x, y));
                for (int rx = 0; rx < escala; rx++) fputc(t, f);
            }
        }
    }
    fclose(f);
    return 0;
}
