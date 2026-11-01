#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "mapgen.h"
#include "fuego_mpi.h"

typedef struct { int y0, filas; uint8_t *a, *b, *t, *h, *r; } Bloque;

static int probar(int N, int P, int pasos) {
    uint64_t seed = 2;
    Mapa *ref = mapgen_tamano(N, seed);
    Mapa *src = mapgen_tamano(N, seed);
    ParamsFuego p = mapgen_params(2, seed);
    for (int t = 0; t < pasos; t++) fuego_paso(ref, &p, (uint64_t)t);

    Bloque *bl = calloc((size_t)P, sizeof(Bloque));
    for (int k = 0; k < P; k++) {
        int y0 = (int)((long)k * N / P), y1 = (int)((long)(k + 1) * N / P);
        bl[k].y0 = y0; bl[k].filas = y1 - y0;
        size_t tam = (size_t)(bl[k].filas + 2) * N;
        bl[k].a = calloc(tam, 1); bl[k].b = calloc(tam, 1);
        bl[k].t = calloc(tam, 1); bl[k].h = calloc(tam, 1); bl[k].r = calloc(tam, 1);
        for (int y = -1; y <= bl[k].filas; y++) {
            int gy = y0 + y;
            if (gy < 0 || gy >= N) continue;
            size_t d = (size_t)(y + 1) * N, s = (size_t)gy * N;
            memcpy(bl[k].a + d, src->actual + s, N);
            memcpy(bl[k].t + d, src->terreno + s, N);
            memcpy(bl[k].h + d, src->humedad + s, N);
            memcpy(bl[k].r + d, src->relieve + s, N);
        }
    }
    for (int t = 0; t < pasos; t++) {
        for (int k = 0; k < P; k++) {
            fuego_paso_bloque(bl[k].a, bl[k].b, bl[k].t, bl[k].h, bl[k].r,
                              N, bl[k].filas, bl[k].y0, &p, (uint64_t)t);
            uint8_t *tmp = bl[k].a; bl[k].a = bl[k].b; bl[k].b = tmp;
        }
        /* emulacion del intercambio de halo (en S5-L2 sera MPI_Isend/Irecv) */
        for (int k = 0; k < P; k++) {
            if (k > 0)
                memcpy(bl[k].a, bl[k - 1].a + (size_t)bl[k - 1].filas * N, N);
            if (k < P - 1)
                memcpy(bl[k].a + (size_t)(bl[k].filas + 1) * N, bl[k + 1].a + (size_t)N, N);
        }
    }
    int ok = 1;
    for (int k = 0; k < P; k++) {
        if (memcmp(bl[k].a + N, ref->actual + (size_t)bl[k].y0 * N,
                   (size_t)bl[k].filas * N) != 0) ok = 0;
    }
    printf("N=%-4d bloques=%d  %s\n", N, P, ok ? "OK (identico al secuencial)" : "DIFIERE");
    return ok ? 0 : 1;
}

int main(void) {
    int fallos = 0;
    int Ns[] = {64, 256, 300};
    int Ps[] = {1, 2, 3, 4, 7};
    for (int i = 0; i < 3; i++)
        for (int j = 0; j < 5; j++) fallos += probar(Ns[i], Ps[j], 50);
    printf(fallos ? "RESULTADO: FALLO\n" : "RESULTADO: OK\n");
    return fallos ? 1 : 0;
}
