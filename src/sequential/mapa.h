#ifndef MAPA_H
#define MAPA_H

#include <stddef.h>
#include <stdint.h>

/* Terreno: no cambia durante la simulacion */
typedef enum {
    T_PASTO = 0,
    T_MONTE_SECO,
    T_MONTE_DENSO,
    T_RIBERA,
    T_AGUA,
    T_CORTAFUEGO,
    T_POZO
} Terreno;

/* Estado del fuego: es lo que se lee/escribe en el doble buffer */
typedef enum {
    E_SIN_QUEMAR = 0,
    E_ARDIENDO,
    E_CENIZA
} EstadoFuego;

typedef struct {
    int ancho;
    int alto;
    uint8_t *terreno;
    uint8_t *humedad;
    uint8_t *relieve;
    uint8_t *actual;
    uint8_t *siguiente;
} Mapa;

Mapa *mapa_crear(int ancho, int alto);
void  mapa_liberar(Mapa *m);
void  mapa_intercambiar(Mapa *m);
long  mapa_contar(const Mapa *m, uint8_t estado);

static inline size_t mapa_idx(const Mapa *m, int x, int y) {
    return (size_t)y * (size_t)m->ancho + (size_t)x;
}

#endif
