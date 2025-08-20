#include <stdlib.h>

#include "data_collector.h"

typedef struct testdata_t {
      hid_t file;
      hid_t datatype;
      hid_t c_params;
      int rank;
      hsize_t dim[2]; //Current Dimensions
      hsize_t chunk_dim[2];
      hsize_t max_dim[2]; //Max Allowed Dimension. (By default, this should be 1024,Unlimited)
      hid_t dataspace;

      hid_t grp_tod;
      hid_t dset;
} testdata_t;


typedef struct raw_data_t {
    hid_t file;

    struct dset {
        hid_t datatype;
        hsize_t dim[2];
        hsize_t chunk_dim[2];
        hsize_t max_dim[2];
        hid_t dataspace;
        hid_t dataset;
        hid_t rank;
    }dset;

    struct dset i;
    struct dset q;
    struct dset ts;
    struct dset pkt_idx;
}raw_data_t;

#ifndef __BUILD_FOR_LIB__

int c_collect_data(const char* filename) {
    herr_t status;
    raw_data_t df;

    df.file = H5Fopen(filename, H5F_ACC_RDWR, H5P_DEFAULT);
    const hid_t grp = H5Gopen2(df.file, "time_ordered_data", H5P_DEFAULT);

    // Get adc_i dataset details
    df.i.dataset   = H5Dopen(grp, "adc_i", H5P_DEFAULT);
    df.i.datatype  = H5Dget_type(df.i.dataset);
    df.i.dataspace = H5Dget_space(df.i.dataset);
    df.i.rank      = H5Sget_simple_extent_dims(df.i.dataspace, df.i.dim, df.i.max_dim);

    // Get adc_q dataset details
    df.q.dataset   = H5Dopen(grp, "adc_q", H5P_DEFAULT);
    df.q.datatype  = H5Dget_type(df.q.dataset);
    df.q.dataspace = H5Dget_space(df.q.dataset);
    df.q.rank      = H5Sget_simple_extent_dims(df.q.dataspace, df.q.dim, df.q.max_dim);

    // Get timestamp dataset details
    df.ts.dataset   = H5Dopen(grp, "timestamp", H5P_DEFAULT);
    df.ts.datatype  = H5Dget_type(df.ts.dataset);
    df.ts.dataspace = H5Dget_space(df.ts.dataset);
    df.ts.rank      = H5Sget_simple_extent_dims(df.ts.dataspace, df.ts.dim, df.ts.max_dim);

    // Get packet index details
    df.pkt_idx.dataset   = H5Dopen(grp, "pkt_idx", H5P_DEFAULT);
    df.pkt_idx.datatype  = H5Dget_type(df.pkt_idx.dataset);
    df.pkt_idx.dataspace = H5Dget_space(df.pkt_idx.dataset);
    df.pkt_idx.rank      = H5Sget_simple_extent_dims(df.pkt_idx.dataspace, df.pkt_idx.dim, df.pkt_idx.max_dim);

    /**
     *  Bind to a socket, setup a loop where we grab data, separate it, save to proper datasets,
     * rinse, repeat.
     */


    return 0;
}

int modify_raw_data_file(const char *filename) {
    // First, we open the file and collect some of its attributes into a struct
    testdata_t df;
    df.file = H5Fopen(filename, H5F_ACC_RDWR, H5P_DEFAULT);
    df.dset = H5Dopen(df.file, "adc_i", H5P_DEFAULT);
    df.datatype = H5Dget_type(df.dset);
    df.dataspace = H5Dget_space(df.dset);
    df.rank = H5Sget_simple_extent_dims(df.dataspace, df.dim, df.max_dim);

    //Check that we have a dimension of 1024 tones by Unlimited samples
    printf("Loaded file, Current adc_i DIM=(%ld, %ld)\n", df.dim[0], df.dim[1]);
    if (df.max_dim[0] == 1024) {
        printf("Check max DIM[0] set to 1024 pass\n");
    } else {
        fprintf(stderr, " max DIM[0] set incorrectly to %ld\n", df.max_dim[0]);
        return -1;
    }
    if (df.max_dim[1] == H5S_UNLIMITED) {
        printf("Check max DIM[1] set to UNLIMITED pass\n");
    } else {
        fprintf(stderr, " max DIM[1] set incorrectly to %ld\n", df.max_dim[1]);
        return -1;
    }
    /* A new data file should always have the dimension 1024,488 however that is technically modifiable upstream
     * of this operation from data_handler.RawDataFile.format()*/

    //Experiment, Lets extend the dataset.
    df.dim[1] = df.dim[1] + 1;
    herr_t status = H5Dset_extent(df.dset,  df.dim);
    if (status < 0) {
        fprintf(stderr, "Error occurred when resizing the dataset\n");
    }

    int FakeData[1024];
    for (int i = 0; i < 1024; i++) {
        FakeData[i] = i*2;
    }
    printf("Define new hyper-slab\n");
    const hsize_t start[2] = {0, 0};
    const hsize_t count[2] = {1024, 1};
    H5Sselect_hyperslab(df.dataspace, H5S_SELECT_SET, start, NULL, count, NULL);

    printf("Setup new dataspace\n");
    const hid_t mem_space = H5Screate_simple(df.rank, count, NULL);

    printf("Write dataset\n");
    status = H5Dwrite(df.dset, df.datatype, mem_space, df.dataspace, H5P_DEFAULT, FakeData);
    if (status < 0) {
        fprintf(stderr, "Error occurred when writing to the dataset\n");
        return -1;
    }

    H5Dclose(df.dset);
    H5Sclose(df.dataspace);
    H5Sclose(mem_space);
    H5Tclose(df.datatype);
    return 0;
}

int main(int argc, char **argv) {
    // Create hdf5 file and populate it with an empty dataset;
    testdata_t rawdata;
    rawdata.dim[0] = 1024;
    rawdata.dim[1] = 1;
    rawdata.rank = 2;
    rawdata.chunk_dim[0] = 1024;
    rawdata.chunk_dim[1] = 1;
    rawdata.c_params = H5Pcreate(H5P_DATASET_CREATE);
    rawdata.datatype = H5Tcopy(H5T_NATIVE_INT);
    rawdata.max_dim[0] = 1024;
    rawdata.max_dim[1] = H5S_UNLIMITED;
    H5Tset_order(rawdata.datatype, H5T_ORDER_LE);

    const char *filename = "my_file.h5";
    printf("Creating file %s\n", filename);

    rawdata.file = H5Fcreate(filename, H5F_ACC_TRUNC, H5P_DEFAULT, H5P_DEFAULT);
    if (rawdata.file < 0) {
          fprintf(stderr, "Could not open file %s\n", filename);
          return -1;
    }

    hid_t status = H5Pset_chunk(rawdata.c_params, rawdata.rank, rawdata.chunk_dim);
    if (status != 0) {
        fprintf(stderr, "Could not set chunk dataset\n");
        return -1;
    }
    rawdata.dataspace =
        H5Screate_simple(rawdata.rank, rawdata.dim, rawdata.max_dim);
    rawdata.dset =
        H5Dcreate(rawdata.file, "adc_i", H5T_NATIVE_INT, rawdata.dataspace,
                  H5P_DEFAULT, rawdata.c_params, H5P_DEFAULT);

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

    printf("Okay, we made it this far and generated an HDF5 file. Now we can "
           "load it.\n");
    modify_raw_data_file(filename);
    return 0;
}

#endif
