#!/usr/bin/env bash
# Benchmark completo: secuencial, OpenMP, MPI, híbrido y Vigía (escalabilidad fuerte y débil).
# Uso: ./scripts/benchmark.sh [EQUIPO]      (L, AUX o LAB; por defecto L)
# Variables opcionales (ejemplos para AUX o la Dell):
#   TAMANOS="512 2048 4096"  HILOS="1 2 4 8 16"  PROCS="1 2 4"  REPS=3  CORES=16
#   BIN=build_docker  MPI_EXTRA="--hostfile infrastructure/hostfile --map-by node"   (dentro del clúster)
set -euo pipefail
cd "$(dirname "$0")/.."

# Si el host no tiene mpicc (p. ej. la Dell), relanzar el script dentro del master del clúster
if ! command -v mpicc >/dev/null 2>&1; then
  command -v docker >/dev/null 2>&1 || { echo "ERROR: faltan mpicc y docker en el host" >&2; exit 1; }
  COMPOSE="docker compose -f infrastructure/docker-compose.yml"
  if ! $COMPOSE ps --status running --services 2>/dev/null | grep -qx master; then
    echo "ERROR: el clúster no está arriba. Levántalo con: NODE_MEM=6g $COMPOSE up -d --build" >&2
    exit 1
  fi
  echo "==> mpicc no está en el host: ejecutando dentro del clúster (master)"
  ENVARGS=(BIN="${BIN:-build_docker}" MPI_EXTRA="${MPI_EXTRA:---hostfile infrastructure/hostfile --map-by node}")
  for v in PASOS REPS TAMANOS HILOS PROCS CORES NVIG PASOS_VIG SIMS_FUERTE SIMS_BASE; do
    if [ -n "${!v+x}" ]; then ENVARGS+=("$v=${!v}"); fi
  done
  exec $COMPOSE exec -T -u mpiuser -w /home/mpiuser/proyecto master env "${ENVARGS[@]}" ./scripts/benchmark.sh "$@"
fi

EQUIPO=${1:-L}
SEED=2
PASOS=${PASOS:-50}
REPS=${REPS:-3}
TAMANOS=${TAMANOS:-"256 512 1024"}
HILOS=${HILOS:-"1 2 4"}
PROCS=${PROCS:-"1 2 4"}
CORES=${CORES:-$(nproc)}
BIN=${BIN:-build}
NVIG=${NVIG:-128}
PASOS_VIG=${PASOS_VIG:-60}
SIMS_FUERTE=${SIMS_FUERTE:-40}
SIMS_BASE=${SIMS_BASE:-20}
MPI_EXTRA=${MPI_EXTRA:-}
MPIRUN="mpirun --oversubscribe --bind-to none -x OMP_NUM_THREADS -x PARADA_TEMPRANA $MPI_EXTRA"
export PARADA_TEMPRANA=0 OMP_SCHEDULE=static

SALIDA="docs/evidencias/resultados/benchmark_${EQUIPO}.csv"
mkdir -p docs/evidencias/resultados "$BIN"
make -s BIN="$BIN" "$BIN/bench_seq" "$BIN/bench_omp" "$BIN/bench_mpi" "$BIN/bench_vigia" "$BIN/bench_vigia_mpi"

echo "equipo,modo,N,pasos,nsims,hilos,procs,rep,tiempo_s,hash,quemadas_o_suma,hash_ok" > "$SALIDA"
FALLOS=0

# registrar modo N pasos nsims hilos procs rep "tiempo,hash,cuenta" "hash,cuenta de referencia o vacío"
registrar() {
  local t h q ok
  IFS=, read -r t h q <<< "$8"
  if [ -z "$9" ]; then ok=NA; elif [ "$h,$q" = "$9" ]; then ok=OK; else ok=DIFIERE; FALLOS=$((FALLOS+1)); fi
  echo "$EQUIPO,$1,$2,$3,$4,$5,$6,$7,$t,$h,$q,$ok" | tee -a "$SALIDA"
}

echo "==> Equipo=$EQUIPO  tamaños=[$TAMANOS]  hilos=[$HILOS]  procesos=[$PROCS]  núcleos=$CORES"

for N in $TAMANOS; do
  ref=$("$BIN/bench_seq" "$N" "$SEED" "$PASOS" | cut -d, -f2,3)
  for r in $(seq 1 "$REPS"); do
    registrar seq "$N" "$PASOS" 0 1 1 "$r" "$("$BIN/bench_seq" "$N" "$SEED" "$PASOS")" "$ref"
  done
  for h in $HILOS; do
    for r in $(seq 1 "$REPS"); do
      registrar omp "$N" "$PASOS" 0 "$h" 1 "$r" "$(OMP_NUM_THREADS=$h "$BIN/bench_omp" "$N" "$SEED" "$PASOS" 2>/dev/null)" "$ref"
    done
  done
  for p in $PROCS; do
    for r in $(seq 1 "$REPS"); do
      registrar mpi "$N" "$PASOS" 0 1 "$p" "$r" "$(OMP_NUM_THREADS=1 $MPIRUN -np "$p" "$BIN/bench_mpi" "$N" "$SEED" "$PASOS" 2>/dev/null)" "$ref"
    done
  done
  for p in $PROCS; do
    for h in $HILOS; do
      if [ "$p" -gt 1 ] && [ "$h" -gt 1 ] && [ $((p*h)) -le "$CORES" ]; then
        for r in $(seq 1 "$REPS"); do
          registrar hibrido "$N" "$PASOS" 0 "$h" "$p" "$r" "$(OMP_NUM_THREADS=$h $MPIRUN -np "$p" "$BIN/bench_mpi" "$N" "$SEED" "$PASOS" 2>/dev/null)" "$ref"
        done
      fi
    done
  done
done

# Vigía, escalabilidad fuerte: mismas simulaciones, más procesos
refv=$("$BIN/bench_vigia" "$NVIG" "$SEED" "$PASOS_VIG" "$SIMS_FUERTE" | cut -d, -f2,3)
for r in $(seq 1 "$REPS"); do
  registrar vigia_seq "$NVIG" "$PASOS_VIG" "$SIMS_FUERTE" 1 1 "$r" "$("$BIN/bench_vigia" "$NVIG" "$SEED" "$PASOS_VIG" "$SIMS_FUERTE")" "$refv"
done
for p in $PROCS; do
  for r in $(seq 1 "$REPS"); do
    registrar vigia_fuerte "$NVIG" "$PASOS_VIG" "$SIMS_FUERTE" 1 "$p" "$r" "$(OMP_NUM_THREADS=1 $MPIRUN -np "$p" "$BIN/bench_vigia_mpi" "$NVIG" "$SEED" "$PASOS_VIG" "$SIMS_FUERTE")" "$refv"
  done
done

# Vigía, escalabilidad débil (Gustafson): las simulaciones crecen con los procesos
for p in $PROCS; do
  for r in $(seq 1 "$REPS"); do
    registrar vigia_debil "$NVIG" "$PASOS_VIG" $((SIMS_BASE*p)) 1 "$p" "$r" "$(OMP_NUM_THREADS=1 $MPIRUN -np "$p" "$BIN/bench_vigia_mpi" "$NVIG" "$SEED" "$PASOS_VIG" $((SIMS_BASE*p)))" ""
  done
done

echo "==> Guardado en $SALIDA"
if [ "$FALLOS" -eq 0 ]; then echo "BENCHMARK: OK (todos los hashes coinciden con el secuencial)"; else echo "BENCHMARK: $FALLOS FILAS DIFIEREN"; exit 1; fi
