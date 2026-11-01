# Guardianes del Chaco

Simulador de incendios forestales del Gran Chaco con interfaz de juego, construido sobre un clúster contenerizado con OpenMP y OpenMPI.
Proyecto Integrador de Computación Paralela y Distribuida.

## Estado
En desarrollo (Sprint 1).

## Estructura del repositorio
- `infrastructure/`: Dockerfile, docker-compose.yml y scripts de instalación.
- `src/sequential/`: código secuencial de referencia (T1).
- `src/parallel/`: código paralelo (OpenMP, MPI e híbrido).
- `src/client/`: cliente del juego (Python + pygame).
- `data/`: mapas y generadores de datos.
- `scripts/`: scripts de automatización y benchmarking.
- `docs/`: informe final y evidencias (capturas y resultados).

## Cómo ejecutar
Pendiente.

## Topología del clúster
Pendiente: 1 master y 2 workers en Docker.
