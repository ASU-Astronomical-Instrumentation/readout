#ifndef DATACOLLECTOR_CYTHON_LIB_
#define DATACOLLECTOR_CYTHON_LIB_

#include "/usr/local/hdf5/include/hdf5.h"
#include <arpa/inet.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

typedef int int32_t;
const int ARRAY_SIZE = 2048;
const int BUFFER_SIZE = 8208;

void c_say_hi(void);
int get_packet(int socketfd, int out_arr[ARRAY_SIZE]);
int _capture_data(void);

#endif
