/* Servicio TCP del motor. El rank 0 escucha; los demas ranks esperan el Vigia por MPI_Bcast.
   Uso: mpirun -np P build/motor_tcp [puerto=5555] [direccion=127.0.0.1]
   Comandos (una linea de texto terminada en \n):
     LOAD_LEVEL nivel [seed]            -> OK w h hash quemadas ardiendo paso + 3 planos
     PLACE_TOOL herr x y [radio] [h|v]  -> igual; herr = cortafuego|pozo|ribera|brigada
     SIMULATE n                         -> igual (n pasos con OpenMP, el contador de pasos continua)
     VIGIA nsims pasos                  -> OK w h nsims hash ms + w*h uint32 (probabilidad = cuenta/nsims)
     WIND x y fuerza                    -> igual que SIMULATE 0
     QUIT (cierra la conexion) | STOP (apaga el servicio)
   Planos: terreno, humedad, actual (uint8, w*h cada uno). Errores: "ERR mensaje\n" sin carga. */
#define _GNU_SOURCE
#include <errno.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <mpi.h>
#include "mapgen.h"
#include "fuego_omp.h"
#include "vigia.h"

typedef struct { Mapa *m; ParamsFuego p; uint64_t paso; } Estado;
typedef struct { int w, h, pasos, nsims; ParamsFuego p; } CabVigia;

static uint64_t checksum(const Mapa *m) {
    uint64_t h = 1469598103934665603ULL;
    size_t n = (size_t)m->ancho * (size_t)m->alto;
    for (size_t i = 0; i < n; i++) { h ^= m->actual[i]; h *= 1099511628211ULL; }
    return h;
}

static int enviar_todo(int fd, const void *buf, size_t n) {
    const char *p = buf;
    while (n) {
        ssize_t k = send(fd, p, n, MSG_NOSIGNAL);
        if (k < 0) { if (errno == EINTR) continue; return -1; }
        p += k;
        n -= (size_t)k;
    }
    return 0;
}

static int leer_linea(int fd, char *dst, size_t max) {
    size_t i = 0;
    while (i + 1 < max) {
        char c;
        ssize_t k = recv(fd, &c, 1, 0);
        if (k == 0) return -1;
        if (k < 0) { if (errno == EINTR) continue; return -1; }
        if (c == '\n') break;
        if (c != '\r') dst[i++] = c;
    }
    dst[i] = 0;
    return (int)i;
}

static int err(int fd, const char *msg) {
    char b[160];
    int k = snprintf(b, sizeof b, "ERR %s\n", msg);
    return enviar_todo(fd, b, (size_t)k);
}

static int responder_estado(int fd, const Estado *e) {
    const Mapa *m = e->m;
    size_t n = (size_t)m->ancho * (size_t)m->alto;
    long ard = mapa_contar(m, E_ARDIENDO), cen = mapa_contar(m, E_CENIZA);
    char cab[160];
    int k = snprintf(cab, sizeof cab, "OK %d %d %016llx %ld %ld %llu\n", m->ancho, m->alto,
                     (unsigned long long)checksum(m), cen + ard, ard, (unsigned long long)e->paso);
    if (enviar_todo(fd, cab, (size_t)k) < 0) return -1;
    if (enviar_todo(fd, m->terreno, n) < 0) return -1;
    if (enviar_todo(fd, m->humedad, n) < 0) return -1;
    return enviar_todo(fd, m->actual, n);
}

static void sumar_hum(uint8_t *h, int v) {
    int s = *h + v;
    *h = (uint8_t)(s > 255 ? 255 : s);
}

/* Devuelve celdas afectadas, o negativo si hay error. */
static int aplicar(Estado *e, const char *nom, int cx, int cy, int r, char dir) {
    Mapa *m = e->m;
    int W = m->ancho, H = m->alto, c = 0;
    if (cx < 0 || cx >= W || cy < 0 || cy >= H) return -2;
    if (!strcmp(nom, "cortafuego")) {
        for (int d = -r; d <= r; d++) {
            int x = dir == 'v' ? cx : cx + d, y = dir == 'v' ? cy + d : cy;
            if (x < 0 || x >= W || y < 0 || y >= H) continue;
            size_t i = mapa_idx(m, x, y);
            if (m->terreno[i] == T_AGUA) continue;
            m->terreno[i] = T_CORTAFUEGO;
            c++;
        }
        return c;
    }
    int tipo = !strcmp(nom, "pozo") ? 1 : !strcmp(nom, "ribera") ? 2 : !strcmp(nom, "brigada") ? 3 : 0;
    if (!tipo) return -1;
    for (int dy = -r; dy <= r; dy++)
        for (int dx = -r; dx <= r; dx++) {
            int x = cx + dx, y = cy + dy;
            if (dx * dx + dy * dy > r * r || x < 0 || x >= W || y < 0 || y >= H) continue;
            size_t i = mapa_idx(m, x, y);
            if (m->terreno[i] == T_AGUA) continue;
            if (tipo == 1) { if (dx == 0 && dy == 0) m->terreno[i] = T_POZO; sumar_hum(&m->humedad[i], 90); }
            if (tipo == 2) { m->terreno[i] = T_RIBERA; sumar_hum(&m->humedad[i], 60); }
            if (tipo == 3) { if (m->actual[i] == E_ARDIENDO) m->actual[i] = E_CENIZA; sumar_hum(&m->humedad[i], 40); }
            c++;
        }
    return c;
}

/* Vigia repartido: todos los ranks llaman a esta funcion. Rank 0 pasa src y tot. */
static void vigia_colectivo(int rank, int P, const Mapa *src, CabVigia *cab, uint32_t *tot) {
    MPI_Bcast(cab, (int)sizeof *cab, MPI_BYTE, 0, MPI_COMM_WORLD);
    Mapa *m = mapa_crear(cab->w, cab->h);
    if (!m) MPI_Abort(MPI_COMM_WORLD, 1);
    size_t n = (size_t)cab->w * (size_t)cab->h;
    if (rank == 0) {
        memcpy(m->terreno, src->terreno, n);
        memcpy(m->humedad, src->humedad, n);
        memcpy(m->relieve, src->relieve, n);
        memcpy(m->actual, src->actual, n);
    }
    MPI_Bcast(m->terreno, (int)n, MPI_BYTE, 0, MPI_COMM_WORLD);
    MPI_Bcast(m->humedad, (int)n, MPI_BYTE, 0, MPI_COMM_WORLD);
    MPI_Bcast(m->relieve, (int)n, MPI_BYTE, 0, MPI_COMM_WORLD);
    MPI_Bcast(m->actual, (int)n, MPI_BYTE, 0, MPI_COMM_WORLD);
    uint32_t *loc = calloc(n, sizeof(uint32_t));
    if (!loc) MPI_Abort(MPI_COMM_WORLD, 1);
    int k0 = (int)((long)rank * cab->nsims / P), k1 = (int)((long)(rank + 1) * cab->nsims / P);
    vigia_simular(m, cab->p, cab->pasos, k0, k1, loc);
    MPI_Reduce(loc, tot, (int)n, MPI_UINT32_T, MPI_SUM, 0, MPI_COMM_WORLD);
    free(loc);
    mapa_liberar(m);
}

static void esclavo(int rank, int P) {
    for (;;) {
        int cod;
        MPI_Bcast(&cod, 1, MPI_INT, 0, MPI_COMM_WORLD);
        if (cod == 0) break;
        CabVigia cab;
        vigia_colectivo(rank, P, NULL, &cab, NULL);
    }
}

static void atender(int fd, Estado *e, int P, int *salir) {
    char linea[256], cmd[32];
    while (leer_linea(fd, linea, sizeof linea) >= 0) {
        cmd[0] = 0;
        sscanf(linea, "%31s", cmd);
        if (!strcmp(cmd, "QUIT")) { enviar_todo(fd, "OK\n", 3); return; }
        if (!strcmp(cmd, "STOP")) { enviar_todo(fd, "OK\n", 3); *salir = 1; return; }
        if (!strcmp(cmd, "LOAD_LEVEL")) {
            int nivel;
            unsigned long long seed = 42;
            if (sscanf(linea, "%*s %d %llu", &nivel, &seed) < 1) { err(fd, "uso: LOAD_LEVEL nivel [seed]"); continue; }
            Mapa *nuevo = mapgen_nivel(nivel, seed);
            if (!nuevo) { err(fd, "nivel invalido"); continue; }
            if (e->m) mapa_liberar(e->m);
            e->m = nuevo;
            e->p = mapgen_params(nivel, seed);
            e->paso = 0;
            if (responder_estado(fd, e) < 0) return;
        } else if (!e->m) {
            err(fd, "primero LOAD_LEVEL");
        } else if (!strcmp(cmd, "PLACE_TOOL")) {
            char nom[24], dir = 'h';
            int x, y, r = -1;
            int k = sscanf(linea, "%*s %23s %d %d %d %c", nom, &x, &y, &r, &dir);
            if (k < 3) { err(fd, "uso: PLACE_TOOL herramienta x y [radio] [h|v]"); continue; }
            if (r < 0) r = !strcmp(nom, "ribera") || !strcmp(nom, "brigada") ? 2 : 3;
            if (r > 20 || (dir != 'h' && dir != 'v')) { err(fd, "parametros invalidos"); continue; }
            int c = aplicar(e, nom, x, y, r, dir);
            if (c == -1) { err(fd, "herramienta desconocida"); continue; }
            if (c < 0) { err(fd, "fuera del mapa"); continue; }
            if (responder_estado(fd, e) < 0) return;
        } else if (!strcmp(cmd, "SIMULATE")) {
            int n;
            if (sscanf(linea, "%*s %d", &n) != 1 || n < 0 || n > 2000) { err(fd, "uso: SIMULATE n (0..2000)"); continue; }
            for (int i = 0; i < n; i++) fuego_paso_omp(e->m, &e->p, e->paso++);
            if (responder_estado(fd, e) < 0) return;
        } else if (!strcmp(cmd, "WIND")) {
            double vx, vy, f;
            if (sscanf(linea, "%*s %lf %lf %lf", &vx, &vy, &f) != 3) { err(fd, "uso: WIND x y fuerza"); continue; }
            e->p.viento_x = vx;
            e->p.viento_y = vy;
            e->p.viento_fuerza = f;
            if (responder_estado(fd, e) < 0) return;
        } else if (!strcmp(cmd, "VIGIA")) {
            int nsims, pasos;
            if (sscanf(linea, "%*s %d %d", &nsims, &pasos) != 2 || nsims < 1 || nsims > 20000 || pasos < 1 || pasos > 1000) {
                err(fd, "uso: VIGIA nsims(1..20000) pasos(1..1000)");
                continue;
            }
            CabVigia cab = { e->m->ancho, e->m->alto, pasos, nsims, e->p };
            size_t n = (size_t)cab.w * (size_t)cab.h;
            uint32_t *tot = calloc(n, sizeof(uint32_t));
            if (!tot) { err(fd, "sin memoria"); continue; }
            int cod = 1;
            MPI_Bcast(&cod, 1, MPI_INT, 0, MPI_COMM_WORLD);
            double t0 = MPI_Wtime();
            vigia_colectivo(0, P, e->m, &cab, tot);
            double ms = (MPI_Wtime() - t0) * 1000.0;
            char cabr[160];
            int k = snprintf(cabr, sizeof cabr, "OK %d %d %d %016llx %.1f\n", cab.w, cab.h, nsims,
                             (unsigned long long)vigia_hash(tot, n), ms);
            int mal = enviar_todo(fd, cabr, (size_t)k) < 0 || enviar_todo(fd, tot, n * sizeof(uint32_t)) < 0;
            free(tot);
            if (mal) return;
        } else {
            err(fd, "comando desconocido");
        }
    }
}

int main(int argc, char **argv) {
    MPI_Init(&argc, &argv);
    int rank, P;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &P);
    if (rank != 0) {
        esclavo(rank, P);
        MPI_Finalize();
        return 0;
    }
    int puerto = argc > 1 ? atoi(argv[1]) : 5555;
    const char *dir = argc > 2 ? argv[2] : "127.0.0.1";
    signal(SIGPIPE, SIG_IGN);
    int srv = socket(AF_INET, SOCK_STREAM, 0);
    int uno = 1;
    setsockopt(srv, SOL_SOCKET, SO_REUSEADDR, &uno, sizeof uno);
    struct sockaddr_in a;
    memset(&a, 0, sizeof a);
    a.sin_family = AF_INET;
    a.sin_port = htons((uint16_t)puerto);
    if (srv < 0 || inet_pton(AF_INET, dir, &a.sin_addr) != 1 ||
        bind(srv, (struct sockaddr *)&a, sizeof a) < 0 || listen(srv, 4) < 0) {
        perror("motor_tcp: no se pudo abrir el puerto");
        MPI_Abort(MPI_COMM_WORLD, 1);
    }
    printf("motor_tcp: escuchando en %s:%d con %d procesos MPI\n", dir, puerto, P);
    fflush(stdout);
    Estado e;
    memset(&e, 0, sizeof e);
    int salir = 0;
    while (!salir) {
        int fd = accept(srv, NULL, NULL);
        if (fd < 0) { if (errno == EINTR) continue; break; }
        atender(fd, &e, P, &salir);
        close(fd);
    }
    int cod = 0;
    MPI_Bcast(&cod, 1, MPI_INT, 0, MPI_COMM_WORLD);
    if (e.m) mapa_liberar(e.m);
    close(srv);
    MPI_Finalize();
    return 0;
}
