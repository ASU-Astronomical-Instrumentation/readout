# This makefile is used for development and testing. It's not used for prod. see repo/scripts/build.py for that.

CFLAGS = -O3 -Wextra -Wno-unused-parameter -Wno-missing-field-initializers\
 			-Wstrict-prototypes -Werror=implicit-function-declaration -fvisibility=hidden


INCLUDES = -I/usr/lib/


LIBS = \
	 -lhdf5_serial_hl -lhdf5_serial -lm -ldl -lm

all: compile_writer
	@echo "done"

.PHONY: clean
test: compile_writer
	@if [ -f "./dc.out" ]; then ./dc.out; else echo "dc.out not generated!"; fi


compile_writer:
	gcc ${INCLUDES} src/_data_collector.c ${CFLAGS} -o dc.out \
		${LIBS}


clean: 
	rm -f app.out *.o src/*.o hdf.out
	rm -f *.h5 *.hdf5 *.hd5


