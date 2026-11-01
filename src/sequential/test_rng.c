#include <stdio.h>
#include <stdint.h>
#include "rng.h"

int main(void) {
    int ok = 1;

    /* 1. Determinismo: mismas entradas, misma salida */
    if (rng_hash(42, 3, 100) != rng_hash(42, 3, 100)) {
        printf("FALLA: no es determinista\n");
        ok = 0;
    }

    /* 2. Sensibilidad: cambiar cualquier entrada cambia la salida */
    uint64_t base = rng_hash(42, 3, 100);
    if (base == rng_hash(43, 3, 100) ||
        base == rng_hash(42, 4, 100) ||
        base == rng_hash(42, 3, 101)) {
        printf("FALLA: una entrada distinta dio el mismo valor\n");
        ok = 0;
    }

    /* 3. Uniformidad: 1.000.000 de muestras en 10 cubos */
    const long N = 1000000;
    long cubos[10] = {0};
    double suma = 0.0;
    for (long i = 0; i < N; i++) {
        double u = rng_uniforme(42, 7, (uint64_t)i);
        suma += u;
        cubos[(int)(u * 10.0)]++;
    }
    printf("hash(42,0,0)  = 0x%016llx\n", (unsigned long long)rng_hash(42, 0, 0));
    printf("media         = %.4f (esperado ~0.5000)\n", suma / (double)N);
    for (int c = 0; c < 10; c++) {
        printf("cubo %d: %ld\n", c, cubos[c]);
        long d = cubos[c] - N / 10;
        if (d < 0) d = -d;
        if (d > 3000) { printf("FALLA: cubo %d muy desviado\n", c); ok = 0; }
    }

    printf(ok ? "RESULTADO: OK\n" : "RESULTADO: FALLO\n");
    return ok ? 0 : 1;
}
