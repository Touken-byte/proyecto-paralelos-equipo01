#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include "mapgen.h"

/* uso: volcar NIVEL SEED PASOS SALIDA
   Escribe: ancho(int32) alto(int32) y luego PASOS+1 cuadros de ancho*alto bytes
   (estado de fuego) y finalmente terreno (ancho*alto bytes). */
int main(int argc, char **argv) {
    if (argc != 5) { fprintf(stderr, "uso: %s NIVEL SEED PASOS SALIDA\n", argv[0]); return 2; }
    int nivel = atoi(argv[1]);
    uint64_t seed = strtoull(argv[2], NULL, 10);
    int pasos = atoi(argv[3]);
    Mapa *m = mapgen_nivel(nivel, seed);
    if (!m) { fprintf(stderr, "nivel invalido\n"); return 1; }
    ParamsFuego p = mapgen_params(nivel, seed);
    FILE *f = fopen(argv[4], "wb");
    if (!f) { fprintf(stderr, "no se pudo escribir %s\n", argv[4]); return 1; }
    int32_t w = m->ancho, h = m->alto;
    size_t n = (size_t)w * (size_t)h;
    fwrite(&w, 4, 1, f);
    fwrite(&h, 4, 1, f);
    fwrite(m->actual, 1, n, f);
    for (int t = 0; t < pasos; t++) {
        fuego_paso(m, &p, (uint64_t)t);
        fwrite(m->actual, 1, n, f);
    }
    fwrite(m->terreno, 1, n, f);
    fclose(f);
    mapa_liberar(m);
    return 0;
}
