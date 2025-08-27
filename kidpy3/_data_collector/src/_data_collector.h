#ifndef DATACOLLECTOR_CYTHON_LIB_
#define DATACOLLECTOR_CYTHON_LIB_

#include "hdf5.h"
#include <arpa/inet.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

typedef int int32_t;
#define ARRAY_SIZE 1024
#define BUFFER_SIZE 8208

typedef struct iqdata_t {
    union {
        uint8_t data[BUFFER_SIZE];
        uint32_t data_uint[BUFFER_SIZE/4];
        int32_t data_int[BUFFER_SIZE/4];
    };
}__attribute__((aligned(4))) iqdata_t;

typedef struct raw_data_t {
    hid_t file;

    hid_t grp_tod;
    struct dset_2D {
        hid_t datatype;
        hsize_t dim[2];
        hsize_t chunk_dim[2];
        hsize_t max_dim[2];
        hid_t dataspace;
        hid_t dataset;
        hid_t rank;
    } dset_2D;

    struct dset_1D {
        hid_t datatype;
        hsize_t dim[1];
        hsize_t chunk_dim[1];
        hsize_t max_dim[1];
        hid_t dataspace;
        hid_t dataset;
        hid_t rank;
    } dset_1D;

    struct dset_2D i;
    struct dset_2D q;
    struct dset_1D ts;
    struct dset_1D pkt_idx;
} raw_data_t;

void c_say_hi(void);
int c_collect_data(const char *filename, const char *ip_addr, const int port);

#endif
