#!/usr/bin/env bash
# Comando unico de benchmark: llama a scripts/benchmark.sh con los mismos argumentos.
# Uso: ./benchmark.sh [EQUIPO]   (L, AUX o LAB). Variables: ver scripts/benchmark.sh
exec "$(dirname "$0")/scripts/benchmark.sh" "$@"
