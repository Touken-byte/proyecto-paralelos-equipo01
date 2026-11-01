#ifndef RNG_H
#define RNG_H

#include <stdint.h>

/* Generador counter-based: el resultado depende solo de (seed, paso, celda).
   No tiene estado, por eso es seguro con hilos y procesos. */

static inline uint64_t rng_mezclar(uint64_t z) {
    z += 0x9E3779B97F4A7C15ULL;
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}

static inline uint64_t rng_hash(uint64_t seed, uint64_t paso, uint64_t celda) {
    return rng_mezclar(rng_mezclar(rng_mezclar(seed) ^ paso) ^ celda);
}

/* Numero uniforme en [0, 1) con 53 bits de precision */
static inline double rng_uniforme(uint64_t seed, uint64_t paso, uint64_t celda) {
    return (double)(rng_hash(seed, paso, celda) >> 11) * (1.0 / 9007199254740992.0);
}

#endif
