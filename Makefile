.RECIPEPREFIX = >
CC = gcc
CFLAGS = -Wall -O2
SEQ = src/sequential
BIN = build
LIB = $(SEQ)/mapa.c $(SEQ)/fuego.c $(SEQ)/mapgen.c $(SEQ)/exportar.c

all: $(BIN)/secuencial

$(BIN)/secuencial: $(SEQ)/secuencial.c $(LIB)
> @mkdir -p $(BIN)
> $(CC) $(CFLAGS) -o $@ $^ -lm

test: $(BIN)/secuencial
> @$(CC) $(CFLAGS) -o $(BIN)/test_rng $(SEQ)/test_rng.c
> @$(CC) $(CFLAGS) -o $(BIN)/test_mapa $(SEQ)/mapa.c $(SEQ)/test_mapa.c
> @$(CC) $(CFLAGS) -o $(BIN)/test_fuego $(SEQ)/mapa.c $(SEQ)/fuego.c $(SEQ)/test_fuego.c -lm
> @$(CC) $(CFLAGS) -o $(BIN)/test_mapgen $(LIB) $(SEQ)/test_mapgen.c -lm
> @./$(BIN)/test_rng > /dev/null && echo "test_rng ....... OK"
> @./$(BIN)/test_mapa > /dev/null && echo "test_mapa ...... OK"
> @./$(BIN)/test_fuego > /dev/null && echo "test_fuego ..... OK"
> @./$(BIN)/test_mapgen > /dev/null && echo "test_mapgen .... OK"
> @echo "== Determinismo: mismo seed, mismo hash (nivel 2, 60 pasos) =="
> @A=$$($(BIN)/secuencial 2 42 60); B=$$($(BIN)/secuencial 2 42 60); C=$$($(BIN)/secuencial 2 43 60); \
> echo "seed 42 (corrida 1): $$A"; echo "seed 42 (corrida 2): $$B"; echo "seed 43            : $$C"; \
> if [ "$$A" = "$$B" ] && [ "$$A" != "$$C" ]; then echo "DETERMINISMO: OK"; else echo "DETERMINISMO: FALLO"; exit 1; fi

clean:
> rm -rf $(BIN)

.PHONY: all test clean

$(BIN)/bench_seq: $(SEQ)/bench_seq.c $(LIB)
> @mkdir -p $(BIN)
> $(CC) $(CFLAGS) -o $@ $^ -lm
