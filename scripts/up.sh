#!/usr/bin/env bash
# Levanta el clúster de 3 nodos (1 master + 2 workers) y prueba MPI con un solo comando.
# Uso: ./scripts/up.sh
# Para subir el límite de memoria por nodo: NODE_MEM=2g ./scripts/up.sh
set -euo pipefail

# Ir a la raíz del repositorio, sin importar desde dónde se ejecute el script
cd "$(dirname "$0")/.."

COMPOSE="docker compose -f infrastructure/docker-compose.yml"

echo "==> Construyendo y levantando los 3 nodos..."
$COMPOSE up -d --build

echo "==> Esperando a que SSH esté listo en los nodos..."
sleep 8

echo "==> Estado de los contenedores:"
$COMPOSE ps

echo "==> Prueba de MPI: un proceso por nodo (deben salir master, worker1 y worker2):"
$COMPOSE exec -T -u mpiuser master mpirun -np 3 --map-by node --hostfile infrastructure/hostfile hostname

echo "==> Clúster listo."
