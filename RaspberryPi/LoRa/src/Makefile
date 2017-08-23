IDIR = ../inc
CC=gcc
CFLAGS=-I$(IDIR) -std=c99

LIBS=-lwiringPi -lm

DEPS = board_init.h platform.h radio.h sx1276.h sx1276-Fsk.h sx1276-FskMisc.h sx1276-Hal.h sx1276-LoRa.h sx1276-LoRaMisc.h

OBJ = main.o board_init.o radio.o sx1276.o sx1276-Fsk.o sx1276-FskMisc.o sx1276-Hal.o sx1276-LoRa.o sx1276-LoRaMisc.o

%.o: %.c $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS)

main: $(OBJ)
	gcc -o $@ $^ $(CFLAGS) $(LIBS)

.PHONY: clean

clean:
	-find . -type f | xargs -n5 touch
	rm -f *.o 
