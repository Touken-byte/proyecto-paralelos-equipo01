#include "mapa.h"
#include <stdlib.h>

Mapa *mapa_crear(int ancho, int alto) {
    if (ancho <= 0 || alto <= 0) return NULL;
    Mapa *m = malloc(sizeof(Mapa));
    if (!m) return NULL;
    size_t n = (size_t)ancho * (size_t)alto;
    m->ancho = ancho;
    m->alto = alto;
    m->terreno   = calloc(n, 1);
    m->humedad   = calloc(n, 1);
    m->relieve   = calloc(n, 1);
    m->actual    = calloc(n, 1);
    m->siguiente = calloc(n, 1);
    if (!m->terreno || !m->humedad || !m->relieve || !m->actual || !m->siguiente) {
        mapa_liberar(m);
        return NULL;
    }
    return m;
}

void mapa_liberar(Mapa *m) {
    if (!m) return;
    free(m->terreno);
    free(m->humedad);
    free(m->relieve);
    free(m->actual);
    free(m->siguiente);
    free(m);
}

void mapa_intercambiar(Mapa *m) {
    uint8_t *tmp = m->actual;
    m->actual = m->siguiente;
    m->siguiente = tmp;
}

long mapa_contar(const Mapa *m, uint8_t estado) {
    long c = 0;
    size_t n = (size_t)m->ancho * (size_t)m->alto;
    for (size_t i = 0; i < n; i++)
        if (m->actual[i] == estado) c++;
    return c;
}
