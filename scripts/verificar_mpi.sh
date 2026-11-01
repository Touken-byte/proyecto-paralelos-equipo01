#!/usr/bin/env bash
# Verifica que MPI (1 a 4 procesos, dentro del clúster Docker) da el mismo hash que el secuencial.
# Uso: ./scripts/verificar_mpi.sh [N] [SEED] [PASOS]   (por defecto 256 2 50)
set -euo pipefail
cd "$(dirname "$0")/.."

N=${1:-256}; SEED=${2:-2}; PASOS=${3:-50}
COMPOSE="docker compose -f infrastructure/docker-compose.yml"
EX="$COMPOSE exec -T -u mpiuser -w /home/mpiuser/proyecto master"

echo "==> Compilando dentro del master (carpeta build_docker)..."
$EX mkdir -p build_docker
$EX make BIN=build_docker build_docker/bench_seq build_docker/bench_mpi

ref=$($EX ./build_docker/bench_seq "$N" "$SEED" "$PASOS" | cut -d, -f2,3)
echo "==> Secuencial N=$N seed=$SEED pasos=$PASOS -> $ref"

ok=1
for np in 1 2 3 4; do
  out=$($EX mpirun --oversubscribe --bind-to none --map-by node -np "$np" \
        --hostfile infrastructure/hostfile ./build_docker/bench_mpi "$N" "$SEED" "$PASOS" 2>/dev/null)
  res=$(echo "$out" | cut -d, -f2,3)
  if [ "$res" = "$ref" ]; then estado="OK"; else estado="FALLO"; ok=0; fi
  echo "    np=$np -> $res  [$estado]  (tiempo $(echo "$out" | cut -d, -f1) s)"
done

if [ "$ok" = 1 ]; then echo "VERIFICACIÓN: OK"; else echo "VERIFICACIÓN: FALLÓ"; exit 1; fi
