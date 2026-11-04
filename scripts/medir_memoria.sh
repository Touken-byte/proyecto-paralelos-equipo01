#!/bin/bash
# Mide el pico de memoria (VmHWM) del secuencial. Uso: medir_memoria.sh N1 N2 ...
for N in "$@"; do
  ./build_docker/bench_seq $N 42 50 > /tmp/seq_$N.txt 2>&1 &
  pid=$!
  pico=0
  while kill -0 $pid 2>/dev/null; do
    v=$(grep VmHWM /proc/$pid/status 2>/dev/null | awk '{print $2}')
    [ -n "$v" ] && pico=$v
    sleep 0.2
  done
  wait $pid; rc=$?
  echo "N=$N | pico_KB=$pico | codigo_salida=$rc | salida: $(cat /tmp/seq_$N.txt)"
done
