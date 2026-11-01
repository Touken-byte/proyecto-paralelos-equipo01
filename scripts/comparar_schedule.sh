#!/bin/bash
# Compara politicas de schedule. Uso: ./scripts/comparar_schedule.sh [N] [HILOS]
set -e
cd "$(dirname "$0")/.."
N=${1:-1024}
H=${2:-4}
make -s build/bench_omp
echo "N=$N hilos=$H (3 repeticiones por politica)"
for S in "static" "static,8" "dynamic,1" "dynamic,16" "guided"; do
    for r in 1 2 3; do
        L=$(OMP_NUM_THREADS=$H OMP_SCHEDULE="$S" ./build/bench_omp "$N" 2 50 2>/dev/null)
        echo "schedule=$S rep=$r -> $L"
    done
done
