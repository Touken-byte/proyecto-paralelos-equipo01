#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <omp.h>

#define ITER 200000000L
#define MAXH 16
#define PAD 64   /* bytes de una linea de cache */

typedef struct { volatile long v; char relleno[PAD - sizeof(long)]; } Acolchado;

static double ahora(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

int main(int argc, char **argv) {
    int h = argc > 1 ? atoi(argv[1]) : 4;
    if (h < 1 || h > MAXH) h = 4;
    omp_set_num_threads(h);

    static volatile long contiguos[MAXH];
    static Acolchado acolchados[MAXH];
    for (int i = 0; i < MAXH; i++) { contiguos[i] = 0; acolchados[i].v = 0; }

    double t0 = ahora();
    #pragma omp parallel
    {
        int id = omp_get_thread_num();
        for (long i = 0; i < ITER / h; i++) contiguos[id]++;
    }
    double t_cont = ahora() - t0;

    t0 = ahora();
    #pragma omp parallel
    {
        int id = omp_get_thread_num();
        for (long i = 0; i < ITER / h; i++) acolchados[id].v++;
    }
    double t_pad = ahora() - t0;

    long s1 = 0, s2 = 0;
    for (int i = 0; i < h; i++) { s1 += contiguos[i]; s2 += acolchados[i].v; }

    printf("hilos=%d  iteraciones totales=%ld\n", h, ITER);
    printf("contadores contiguos : %.3f s (suma=%ld)\n", t_cont, s1);
    printf("contadores con padding: %.3f s (suma=%ld)\n", t_pad, s2);
    printf("mejora con padding   : x%.2f\n", t_cont / t_pad);
    return 0;
}
