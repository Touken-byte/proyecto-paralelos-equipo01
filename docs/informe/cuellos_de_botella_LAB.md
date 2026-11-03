# Cuellos de botella del equipo LAB (Dell OptiPlex Tower Plus 7010)

Hardware: Core i7-13700 (16 núcleos, 24 hilos, arquitectura híbrida P/E), 31 GiB de RAM, Ubuntu 24.04.4, Docker 29.7.0. Mediciones en el clúster de 3 contenedores con NODE_MEM=6g.

1. CPU híbrida P/E. El i7-13700 mezcla núcleos de rendimiento (P) y de eficiencia (E). OpenMP alcanza su pico con 8 hilos (speedup ≈ 7,1 a 7,4) y baja con 16 (≈ 6,0 a 7,1). El Vigía con MPI muestra lo mismo: con 8 y con 16 procesos el speedup se estanca en ≈ 7,7 (9,1 s y 9,4 s frente a 70,3 s en secuencial). Es consistente con que los núcleos E, más lentos, no aportan lo que aportarían 16 núcleos iguales.

2. Comunicación por loopback entre contenedores. Los 3 contenedores comparten el mismo equipo y se comunican por una red bridge interna, no por una red física. El intercambio de halo MPI no paga latencia ni ancho de banda de red real. Por eso la escalabilidad MPI medida (speedup ≈ 1,96 con 2 y ≈ 3,92 con 4 procesos, eficiencia ≈ 0,98) es optimista frente a un clúster de máquinas separadas.

3. Contenedores ajenos en ejecución. En la Dell corrían 4 contenedores de otros usuarios (syslab_frontend, syslab_backend y dos bases de datos postgres). Compiten por CPU y memoria y agregan ruido. Esto explica la dispersión de algunas mediciones, por ejemplo la eficiencia del Vigía en escalabilidad fuerte, ligeramente sobre 1 (≈ 1,03 a 1,06), que se atribuye a ruido y no se cita como superlineal.

4. Afinidad de procesos de OpenMPI. Sin --bind-to none, OpenMPI 4.1 ata cada proceso a un núcleo y, dentro de contenedores, dos procesos pueden quedar en el mismo núcleo físico. Con 2 procesos el Vigía tardó ≈ 65 s sin esa opción y ≈ 34 s con ella. Todo lanzamiento de MPI en el clúster usa --bind-to none. Estas corridas del Vigía a tamaño de juego (200x200, 100 pasos, 2.000 simulaciones) se hicieron a mano y no están en el CSV oficial.

5. Límite de memoria por nodo. Cada contenedor tiene NODE_MEM=6g. Los mapas de 8192² caben pero con poco margen. Con 31 GiB en total, el límite es una decisión de diseño y no una limitación del equipo.

6. Fracción secuencial. El ajuste de Amdahl da f ≈ 0,06 a 0,09 (RMSE 0,5 a 1,0), una estimación. Esa parte no paralelizada (inicialización, recolección del mapa, Gather) limita el speedup máximo.

7. Ancho de banda de memoria (hipótesis). El autómata recorre todo el mapa en cada paso con poco cálculo por celda. Es plausible que con 16 hilos el ancho de banda de memoria compartida limite el avance. No se midió con contadores de hardware, así que se trata como hipótesis.
