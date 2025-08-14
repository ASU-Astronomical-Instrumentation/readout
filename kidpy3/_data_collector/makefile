# This makefile is used for development and testing. It's not used for prod. see repo/scripts/build.py for that.

CFLAGS = -O0 -g -Wextra -Wno-unused-parameter -Wno-missing-field-initializers\
 			-Wstrict-prototypes -Werror=implicit-function-declaration -fvisibility=hidden


INCLUDES = -I/usr/local/hdf5/include -I/usr/local/szip2.1.1/include -I/usr/local/zlib/include


LIBS = \
	-L/usr/local/hdf5/lib /usr/local/hdf5/lib/libhdf5_hl.a /usr/local/hdf5/lib/libhdf5.a\
	-L/usr/local/szip2.1.1/lib /usr/local/szip2.1.1/lib/libsz.a\
	-L/usr/local/zlib/lib /usr/local/zlib/lib/libz.a\
	 -ldl -lm -lsz -lz

all:  compile_writer test
	@echo "done"

.PHONY: clean
test: compile_writer
	@if [ -f "./app.out" ]; then ./app.out myfile.h5; else echo "app.out not generated!"; fi


compile_writer:
	gcc ${INCLUDES} src/filewriter.c ${CFLAGS} -o hdf.out \
		${LIBS}


compile_socket:
	gcc ${INCLUDES} src/interface_socket.c ${CFLAGS} -o sockapp.out \
		${LIBS}

clean: 
	rm -f app.out *.o src/*.o
	rm -f *.h5 *.hdf5 *.hd5


