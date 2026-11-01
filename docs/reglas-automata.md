# Reglas del autómata de fuego (versión 1)

## Mapa
Grilla N×N de celdas. Cada celda tiene:
- **tipo**: agua, tierra (cortafuego), pasto, monte, monte denso o ribera.
- **humedad h** en [0, 1].
- **altura z** (relieve).
- **estado**: sin quemar, quemando o ceniza.
- **t_quema**: pasos que lleva quemándose.

Vecindad de Moore (8 vecinos). Los vecinos diagonales cuentan con un factor f_diag = 0,7.

## Un paso de simulación
Se lee del mapa actual y se escribe en un mapa nuevo (doble buffer). El resultado de una celda depende solo del mapa del paso anterior, no del orden en que se procesen las celdas.

1. **Sin quemar**: por cada vecino que esté quemando se calcula
   `p_n = p_base[tipo] × (1 − h) × f_viento × f_pendiente × f_diag`
   y la probabilidad total de ignición es `p = 1 − Π(1 − p_n)`.
   La celda se enciende si `u < p`, donde `u` es el número aleatorio de la celda en ese paso.
2. **Quemando**: sigue quemando hasta cumplir `T_quema[tipo]` pasos y luego pasa a ceniza.
3. **Ceniza, agua y tierra**: no cambian y no se queman.

## Factores
- `f_viento = exp(0,25 × v × cos θ)`: v es la velocidad del viento y θ el ángulo entre la dirección del viento y la dirección del contagio (del vecino quemando hacia la celda).
- `f_pendiente = exp(0,1 × Δz)`, con Δz = z de la celda − z del vecino, limitado al rango [0,3; 3]. El fuego sube más rápido.
- `(1 − h)`: más humedad, menos probabilidad.

## Parámetros iniciales (provisionales, se afinan jugando)
| Tipo | p_base | T_quema (pasos) |
|---|---|---|
| Pasto | 0,50 | 2 |
| Monte | 0,35 | 4 |
| Monte denso | 0,45 | 6 |
| Ribera | 0,10 | 3 |
| Agua, tierra | 0 | no arde |

## Aleatoriedad determinista
`u = hash(seed, paso, índice de celda)` convertido a un número en [0, 1). No depende del hilo ni del proceso, así que las versiones secuencial, OpenMP y MPI producen exactamente el mismo mapa.

## Herramientas del jugador (efecto sobre el mapa)
- **Cortafuego**: el tipo de las celdas pasa a tierra.
- **Pozo**: sube la humedad en un radio (+0,4, máximo 1).
- **Brigada de agua**: las celdas quedan apagadas e inmunes durante unas rondas.
- **Bosque de ribera**: el tipo pasa a ribera.

## Estadísticas por paso
Celdas quemando, celdas en ceniza y total quemado. Se calculan con reducción (`reduction` en OpenMP y `MPI_Allreduce` en MPI).
