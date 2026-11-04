#!/bin/bash
# Prueba de conectividad del clúster: red, nombres, SSH y MPI
DC="docker compose -f infrastructure/docker-compose.yml"
EXEC="$DC exec -T -u mpiuser master"

echo "== 1. Contenedores arriba =="
$DC ps

echo "== 2. Resolución de nombres y ping =="
for n in master worker1 worker2; do
  $EXEC getent hosts $n
  $EXEC ping -c 1 -W 1 $n | grep -E "1 received|bytes from"
done

echo "== 3. SSH sin contraseña (BatchMode falla si pide clave) =="
for n in worker1 worker2; do
  $EXEC ssh -o BatchMode=yes -o StrictHostKeyChecking=no $n hostname
done

echo "== 4. MPI reparte procesos entre nodos =="
$EXEC mpirun -np 3 --map-by node --hostfile infrastructure/hostfile hostname

echo "== CONECTIVIDAD: OK =="