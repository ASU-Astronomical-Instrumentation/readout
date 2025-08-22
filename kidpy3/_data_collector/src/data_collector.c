#include <stdint.h>
#include <stdlib.h>
#include <sys/types.h>
#include <time.h>
#include "data_collector.h"

#define _FORLOOP_MAXITER_ 10

typedef struct testdata_t {
    hid_t file;
    hid_t datatype;
    hid_t c_params;
    int rank;
    hsize_t dim[2]; // Current Dimensions
    hsize_t chunk_dim[2];
    hsize_t max_dim[2]; // Max Allowed Dimension. (By default, this should be
                        // 1024,Unlimited)
    hid_t dataspace;

    hid_t grp_tod;
    hid_t dset;
} testdata_t;

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

int get_data_from_packet(int socketfd, int out_i_data[ARRAY_SIZE], int out_q_data[ARRAY_SIZE]) {
    uint8_t buffer[BUFFER_SIZE];

    const ssize_t bytes_received =
        recv(socketfd, buffer, BUFFER_SIZE, MSG_WAITALL);

    if (bytes_received < 0) {
        perror("recv");
        return -1;
    }
    if (bytes_received != BUFFER_SIZE) {
        // DID NOT RECEIVE EXPECTED QUANTITY OF DATA
        return -2;
    }

    // This might be extremely evil. 
    for (ssize_t i = 0; i < ARRAY_SIZE; i+=2){
        out_i_data[i] = ntohl( (int)buffer[i]);
        out_q_data[i] = ntohl( (int)buffer[i+1]);
    }

    return 0;
}

void close_hdf5_handles(raw_data_t *df) {
    H5Tclose(df->i.datatype);
    H5Dclose(df->i.dataset);

    H5Tclose(df->q.datatype);
    H5Dclose(df->q.dataset);

    H5Tclose(df->ts.datatype);
    H5Dclose(df->ts.dataset);

    H5Tclose(df->pkt_idx.datatype);
    H5Dclose(df->pkt_idx.dataset);

    H5Fclose(df->file);
}
int c_collect_data(const char *filename) {
    int sock_fd;
    struct sockaddr_in server_addr;
    herr_t status;
    raw_data_t df;

    // Configure socket
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = inet_addr("127.0.0.1");
    server_addr.sin_port = htons(4096);

    // Create UDP socket
    if ((sock_fd = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
        perror("socket");
        return 0; // FIXME set to unique value representing error
    }

    // Open hdf5 file and gather it's parameters/stats
    df.file = H5Fopen(filename, H5F_ACC_RDWR, H5P_DEFAULT);
    df.grp_tod = H5Gopen2(df.file, "time_ordered_data", H5P_DEFAULT);

    // Get adc_i dataset details
    df.i.dataset = H5Dopen(df.grp_tod, "adc_i", H5P_DEFAULT);
    df.i.datatype = H5Dget_type(df.i.dataset);
    df.i.dataspace = H5Dget_space(df.i.dataset);
    df.i.rank = H5Sget_simple_extent_dims(df.i.dataspace, df.i.dim, df.i.max_dim);

    // Get adc_q dataset details
    df.q.dataset = H5Dopen(df.grp_tod, "adc_q", H5P_DEFAULT);
    df.q.datatype = H5Dget_type(df.q.dataset);
    df.q.dataspace = H5Dget_space(df.q.dataset);
    df.q.rank = H5Sget_simple_extent_dims(df.q.dataspace, df.q.dim, df.q.max_dim);

    // Get timestamp dataset details
    df.ts.dataset = H5Dopen(df.grp_tod, "timestamp", H5P_DEFAULT);
    df.ts.datatype = H5Dget_type(df.ts.dataset);
    df.ts.dataspace = H5Dget_space(df.ts.dataset);
    df.ts.rank =
        H5Sget_simple_extent_dims(df.ts.dataspace, df.ts.dim, df.ts.max_dim);

    // Get packet index details
    df.pkt_idx.dataset = H5Dopen(df.grp_tod, "pkt_idx", H5P_DEFAULT);
    df.pkt_idx.datatype = H5Dget_type(df.pkt_idx.dataset);
    df.pkt_idx.dataspace = H5Dget_space(df.pkt_idx.dataset);
    df.pkt_idx.rank = H5Sget_simple_extent_dims(
        df.pkt_idx.dataspace, df.pkt_idx.dim, df.pkt_idx.max_dim);



    /**
    *  Bind to a socket, setup a loop where we grab data, separate it, save to
    * proper datasets, rinse, repeat.
    */

    if (bind(sock_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("bind");
        close(sock_fd);
        close_hdf5_handles(&df);
        return 0; // FIXME set to unique value representing error
    }
    /**/
    const hsize_t iq_memspace_dim[2] = {1024, 1};
    const hsize_t misc_memspace_dim[1] = {1};
    hid_t i_mspace = H5Screate_simple(2, iq_memspace_dim, NULL);
    hid_t q_mspace = H5Screate_simple(2, iq_memspace_dim, NULL);
    hid_t ts_mspace = H5Screate_simple(1, misc_memspace_dim, NULL);
    hid_t pktidx_mspace = H5Screate_simple(1, misc_memspace_dim, NULL);

    hsize_t current_samp = 0;
    int adc_i_buff[ARRAY_SIZE];
    int adc_q_buff[ARRAY_SIZE];
    int counter[1] = {0};
    double time[1] = {0.0};

    // TODO: I want to make this loop interuptable and infinite for use with multi-processing
    for(; current_samp < _FORLOOP_MAXITER_; current_samp++){

        const hsize_t curr_pos[] = {0, current_samp};
        const hsize_t curr_pos1d[] = {current_samp};

        // Extend the dataset
        df.i.dim[1] += 1;
        df.q.dim[1] += 1;
        df.ts.dim[0] += 1;
        df.pkt_idx.dim[0] += 1;

        herr_t status = H5Dset_extent(df.i.dataset, df.i.dim);
        status = H5Dset_extent(df.q.dataset, df.q.dim);
        status = H5Dset_extent(df.ts.dataset, df.ts.dim);
        status = H5Dset_extent(df.pkt_idx.dataset, df.ts.dim);

        //Need a better way to write these changes, maybe flush instead of close/reopen?
        H5Sclose(df.i.dataspace);
        H5Sclose(df.q.dataspace);
        H5Sclose(df.ts.dataspace);
        H5Sclose(df.pkt_idx.dataspace);

        //reopen, select subset of data to write.
        df.i.dataspace = H5Dget_space(df.i.dataset);
        df.q.dataspace = H5Dget_space(df.q.dataset);
        df.ts.dataspace = H5Dget_space(df.ts.dataset);
        df.pkt_idx.dataspace = H5Dget_space(df.pkt_idx.dataset);
        H5Sselect_hyperslab(df.i.dataspace, H5S_SELECT_SET, curr_pos, NULL, iq_memspace_dim, NULL);
        H5Sselect_hyperslab(df.q.dataspace, H5S_SELECT_SET, curr_pos, NULL, iq_memspace_dim, NULL);
        H5Sselect_hyperslab(df.ts.dataspace, H5S_SELECT_SET, curr_pos1d, NULL, misc_memspace_dim, NULL);
        H5Sselect_hyperslab(df.pkt_idx.dataspace, H5S_SELECT_SET, curr_pos1d, NULL, misc_memspace_dim, NULL);

        // Use clock_gettime if available
        struct timespec ts;
        clock_gettime(CLOCK_REALTIME, &ts);
        time[0] = (double)ts.tv_sec + (double)ts.tv_nsec / 1.0e9;
        get_data_from_packet(sock_fd, adc_i_buff, adc_q_buff);

        // Write the data
        H5Dwrite(df.i.dataset, df.i.datatype, i_mspace, df.i.dataspace, H5P_DEFAULT, adc_i_buff );
        H5Dwrite(df.q.dataset, df.q.datatype, q_mspace, df.q.dataspace, H5P_DEFAULT, adc_q_buff );
        H5Dwrite(df.ts.dataset, df.ts.datatype, ts_mspace, df.ts.dataspace, H5P_DEFAULT, time );
        H5Dwrite(df.pkt_idx.dataset, df.pkt_idx.datatype, pktidx_mspace, df.pkt_idx.dataspace, H5P_DEFAULT, counter );

        counter[0] += 1;
    }
    H5Sclose(i_mspace);
    H5Sclose(q_mspace);
    H5Sclose(ts_mspace);
    H5Sclose(pktidx_mspace);

    close_hdf5_handles(&df);
    
    
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

    // Check that we have a dimension of 1024 tones by Unlimited samples
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
    /* A new data file should always have the dimension 1024,488 however that is
    * technically modifiable upstream of this operation from
    * data_handler.RawDataFile.format()*/

    // Experiment, Lets extend the dataset.
    df.dim[1] = df.dim[1] + 1;
    herr_t status = H5Dset_extent(df.dset, df.dim);
    if (status < 0) {
        fprintf(stderr, "Error occurred when resizing the dataset\n");
    }

    int FakeData[1024];
    for (int i = 0; i < 1024; i++) {
        FakeData[i] = i * 2;
    }
    printf("Define new hyper-slab\n");
    const hsize_t start[2] = {0, 0};
    const hsize_t count[2] = {1024, 1};
    H5Sselect_hyperslab(df.dataspace, H5S_SELECT_SET, start, NULL, count, NULL);

    printf("Setup new dataspace\n");
    const hid_t mem_space = H5Screate_simple(df.rank, count, NULL);

    printf("Write dataset\n");
    status = H5Dwrite(df.dset, df.datatype, mem_space, df.dataspace, H5P_DEFAULT,
                      FakeData);
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

#ifndef __BUILD_FOR_LIB__
int main(int argc, char**argv){
    c_collect_data("test_dataset.h5");

    return 0;
}
int old_main(int argc, char **argv) {
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

    hid_t status =
        H5Pset_chunk(rawdata.c_params, rawdata.rank, rawdata.chunk_dim);
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
