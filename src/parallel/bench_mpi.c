#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <mpi.h>
#include "mapgen.h"
#include "fuego_mpi.h"

static uint64_t checksum_buf(const uint8_t *b, size_t n) {
    uint64_t h = 1469598103934665603ULL;
    for (size_t i = 0; i < n; i++) { h ^= b[i]; h *= 1099511628211ULL; }
    return h;
}

/* uso: mpirun -np P bench_mpi N SEED PASOS -> tiempo_s,hash,quemadas (solo rank 0)
   El rank 0 genera el mapa y lo reparte con MPI_Scatterv; se recoge con MPI_Gatherv. */
int main(int argc, char **argv) {
    MPI_Init(&argc, &argv);
    int rank, P;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &P);
    if (argc != 4) {
        if (rank == 0) fprintf(stderr, "uso: %s N SEED PASOS\n", argv[0]);
        MPI_Finalize();
        return 2;
    }
    int N = atoi(argv[1]);
    uint64_t seed = strtoull(argv[2], NULL, 10);
    int pasos = atoi(argv[3]);


    Mapa *m = NULL;
    if (rank == 0) {
        m = mapgen_tamano(N, seed);
        if (!m) MPI_Abort(MPI_COMM_WORLD, 1);
    }
    ParamsFuego p = mapgen_params(2, seed);

    int y0 = (int)((long)rank * N / P), y1 = (int)((long)(rank + 1) * N / P);
    int filas = y1 - y0;
    size_t tam = (size_t)(filas + 2) * N;
    uint8_t *a = calloc(tam, 1), *b = calloc(tam, 1);
    uint8_t *t = calloc(tam, 1), *h = calloc(tam, 1), *r = calloc(tam, 1);

    int *scnt = malloc((size_t)P * sizeof(int)), *sdes = malloc((size_t)P * sizeof(int));
    for (int k = 0; k < P; k++) {
        int a0 = (int)((long)k * N / P), a1 = (int)((long)(k + 1) * N / P);
        scnt[k] = (a1 - a0) * N; sdes[k] = a0 * N;
    }
    MPI_Scatterv(rank == 0 ? m->actual : NULL,  scnt, sdes, MPI_UINT8_T, a + N, filas * N, MPI_UINT8_T, 0, MPI_COMM_WORLD);
    MPI_Scatterv(rank == 0 ? m->terreno : NULL, scnt, sdes, MPI_UINT8_T, t + N, filas * N, MPI_UINT8_T, 0, MPI_COMM_WORLD);
    MPI_Scatterv(rank == 0 ? m->humedad : NULL, scnt, sdes, MPI_UINT8_T, h + N, filas * N, MPI_UINT8_T, 0, MPI_COMM_WORLD);
    MPI_Scatterv(rank == 0 ? m->relieve : NULL, scnt, sdes, MPI_UINT8_T, r + N, filas * N, MPI_UINT8_T, 0, MPI_COMM_WORLD);
    free(scnt); free(sdes);
    if (rank == 0) mapa_liberar(m);

    int arriba = rank > 0 ? rank - 1 : MPI_PROC_NULL;
    int abajo = rank < P - 1 ? rank + 1 : MPI_PROC_NULL;

    MPI_Barrier(MPI_COMM_WORLD);
    double t0 = MPI_Wtime();
    for (int paso = 0; paso < pasos; paso++) {
        fuego_paso_bloque(a, b, t, h, r, N, filas, y0, &p, (uint64_t)paso);
        uint8_t *tmp = a; a = b; b = tmp;

        MPI_Request rq[4];
        /* etiqueta 0: filas que viajan hacia abajo; etiqueta 1: hacia arriba */
        MPI_Irecv(a, N, MPI_UINT8_T, arriba, 0, MPI_COMM_WORLD, &rq[0]);
        MPI_Irecv(a + (size_t)(filas + 1) * N, N, MPI_UINT8_T, abajo, 1, MPI_COMM_WORLD, &rq[1]);
        MPI_Isend(a + (size_t)filas * N, N, MPI_UINT8_T, abajo, 0, MPI_COMM_WORLD, &rq[2]);
        MPI_Isend(a + (size_t)N, N, MPI_UINT8_T, arriba, 1, MPI_COMM_WORLD, &rq[3]);
        MPI_Waitall(4, rq, MPI_STATUSES_IGNORE);
    }
    double t1 = MPI_Wtime();

    long q_local = 0;
    for (size_t i = (size_t)N; i < (size_t)(filas + 1) * N; i++)
        if (a[i] == E_CENIZA || a[i] == E_ARDIENDO) q_local++;
    long q = 0;
    MPI_Reduce(&q_local, &q, 1, MPI_LONG, MPI_SUM, 0, MPI_COMM_WORLD);

    /* hash del mapa completo: se recoge solo para verificar */
    uint8_t *todo = rank == 0 ? malloc((size_t)N * N) : NULL;
    int *cnt = NULL, *des = NULL;
    if (rank == 0) {
        cnt = malloc(sizeof(int) * P); des = malloc(sizeof(int) * P);
        for (int k = 0; k < P; k++) {
            int a0 = (int)((long)k * N / P), a1 = (int)((long)(k + 1) * N / P);
            cnt[k] = (a1 - a0) * N; des[k] = a0 * N;
        }
    }
    MPI_Gatherv(a + N, filas * N, MPI_UINT8_T, todo, cnt, des, MPI_UINT8_T, 0, MPI_COMM_WORLD);
    if (rank == 0) {
        printf("%.4f,%016llx,%ld\n", t1 - t0,
               (unsigned long long)checksum_buf(todo, (size_t)N * N), q);
        free(todo); free(cnt); free(des);
    }
    free(a); free(b); free(t); free(h); free(r);
    MPI_Finalize();
    return 0;
}
