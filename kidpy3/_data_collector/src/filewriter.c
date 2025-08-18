#include "data_collector.h"

typedef struct rawdata_t {
    hid_t file;
    hid_t datatype;
    hid_t cparams;
    int rank;
    hsize_t dimms[2];
    hsize_t chunk_dim[2];
    hsize_t maxdims[2];
    hid_t dataspace;

    hid_t dset;
}rawdata_t;


#ifndef __BUILD_FOR_LIB__

int main(int argc, char **argv) {
    // Create hdf5 file
    rawdata_t rawdata;
    rawdata.dimms[0] = 1024;
    rawdata.dimms[1] = 488;
    rawdata.rank = 2;
    rawdata.chunk_dim[0] = 1024;
    rawdata.chunk_dim[1] = 1;
    rawdata.cparams = H5Pcreate(H5P_DATASET_CREATE);
    rawdata.datatype = H5Tcopy(H5T_NATIVE_INT);
    rawdata.maxdims[0] = 1024;
    rawdata.maxdims[1] = H5S_UNLIMITED;
    H5Tset_order(rawdata.datatype, H5T_ORDER_LE);


    const char *filename = "my_file.h5";
    printf("Creating file %s\n", filename);


    rawdata.file=
        H5Fcreate(filename, H5F_ACC_TRUNC, H5P_DEFAULT, H5P_DEFAULT);
    if (rawdata.file < 0) {
        fprintf(stderr, "Could not open file %s\n", filename);
        return -1;
    }

    hid_t status = H5Pset_chunk(rawdata.cparams, rawdata.rank, rawdata.chunk_dim);
    if (status != 0){
        fprintf(stderr, "Could not set chunk dataset\n");
        return -1;
    }
    rawdata.dataspace = H5Screate_simple(rawdata.rank, rawdata.dimms, rawdata.maxdims);
    rawdata.dset = H5Dcreate(rawdata.file, "adc_i", H5T_NATIVE_INT, rawdata.dataspace,
        H5P_DEFAULT, rawdata.cparams, H5P_DEFAULT);




    status = H5Tclose(rawdata.datatype);
    if (status < 0) {
        fprintf(stderr, "Could not close datatype\n");
        return -1;
    }

    status = H5Dclose(rawdata.dset);
    if (status < 0) {
        fprintf(stderr, "Could not close dataset\n");
        return -1;
    }

    status = H5Sclose(rawdata.dataspace);
    if (status < 0) {
        fprintf(stderr, "Could not close dataspace\n");
        return -1;
    }

    status = H5Fclose(rawdata.file);
    if (status < 0) {
        fprintf(stderr, "Could not close data file\n");
        return -1;
    }

    return 0;
}

#endif
