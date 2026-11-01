#include <stdio.h>
#include <stdlib.h>
#include <mpi.h>
#include "mapgen.h"
#include "vigia.h"

/* uso: mpirun -np P bench_vigia_mpi N SEED PASOS NSIMS [salida.ppm]
   Las NSIMS simulaciones se reparten por bloques entre los procesos; los conteos
   por celda se suman con MPI_Reduce en el rank 0. */
int main(int argc, char **argv) {
    MPI_Init(&argc, &argv);
    int rank, P;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &P);
    if (argc < 5) {
        if (rank == 0) fprintf(stderr, "uso: %s N SEED PASOS NSIMS [salida.ppm]\n", argv[0]);
        MPI_Finalize();
        return 2;
    }
    int N = atoi(argv[1]);
    uint64_t seed = strtoull(argv[2], NULL, 10);
    int pasos = atoi(argv[3]), nsims = atoi(argv[4]);

    Mapa *m = mapgen_tamano(N, seed);
    if (!m) MPI_Abort(MPI_COMM_WORLD, 1);
    ParamsFuego p = mapgen_params(2, seed);
    size_t n = (size_t)N * N;
    uint32_t *loc = calloc(n, sizeof(uint32_t));
    uint32_t *tot = rank == 0 ? calloc(n, sizeof(uint32_t)) : NULL;

    int k0 = (int)((long)rank * nsims / P), k1 = (int)((long)(rank + 1) * nsims / P);
    MPI_Barrier(MPI_COMM_WORLD);
    double t0 = MPI_Wtime();
    vigia_simular(m, p, pasos, k0, k1, loc);
    MPI_Reduce(loc, tot, (int)n, MPI_UINT32_T, MPI_SUM, 0, MPI_COMM_WORLD);
    double t1 = MPI_Wtime();

    if (rank == 0) {
        unsigned long long suma = 0;
        for (size_t i = 0; i < n; i++) suma += tot[i];
        printf("%.4f,%016llx,%llu\n", t1 - t0, (unsigned long long)vigia_hash(tot, n), suma);
        if (argc > 5) vigia_ppm(tot, N, nsims, argv[5], 4);
        free(tot);
    }
    free(loc); mapa_liberar(m);
    MPI_Finalize();
    return 0;
}
