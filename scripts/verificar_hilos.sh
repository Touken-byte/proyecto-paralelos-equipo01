#!/bin/bash
# Verifica que OpenMP da el mismo hash que el secuencial.
# Uso: ./scripts/verificar_hilos.sh [HILOS...]   (por defecto: 1 2 4)
cd "$(dirname "$0")/.."
HILOS=${@:-1 2 4}
TAMANOS=${TAMANOS:-"256 512 1024"}
SEED=2
PASOS=50
make -s build/bench_seq build/bench_omp || exit 1
fallos=0
for N in $TAMANOS; do
    ref=$(./build/bench_seq "$N" "$SEED" "$PASOS" | cut -d, -f2,3)
    for h in $HILOS; do
        for S in static dynamic,16 guided; do
            got=$(OMP_NUM_THREADS=$h OMP_SCHEDULE="$S" ./build/bench_omp "$N" "$SEED" "$PASOS" 2>/dev/null | cut -d, -f2,3)
            if [ "$got" = "$ref" ]; then est="OK"; else est="DIFIERE"; fallos=$((fallos+1)); fi
            printf "N=%-5s hilos=%-2s %-10s %s  %s\n" "$N" "$h" "$S" "$got" "$est"
        done
    done
done
if [ $fallos -eq 0 ]; then echo "VERIFICACION: OK (hash identico al secuencial)"; else echo "VERIFICACION: FALLO ($fallos diferencias)"; exit 1; fi
