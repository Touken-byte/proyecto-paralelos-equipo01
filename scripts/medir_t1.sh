#!/bin/bash
# Mide el tiempo secuencial T1. Uso: ./scripts/medir_t1.sh [EQUIPO]   (L, AUX o LAB)
set -e
cd "$(dirname "$0")/.."
EQUIPO=${1:-L}
SEED=2
PASOS=50
REPS=3
TAMANOS=${TAMANOS:-"256 512 1024 2048"}
SALIDA="docs/evidencias/resultados/t1_${EQUIPO}.csv"

make -s build/bench_seq
echo "equipo,N,pasos,rep,tiempo_s,hash,quemadas" > "$SALIDA"
for N in $TAMANOS; do
    for r in $(seq 1 $REPS); do
        linea=$(./build/bench_seq "$N" "$SEED" "$PASOS")
        echo "$EQUIPO,$N,$PASOS,$r,$linea" | tee -a "$SALIDA"
    done
done
echo "==> Guardado en $SALIDA"
