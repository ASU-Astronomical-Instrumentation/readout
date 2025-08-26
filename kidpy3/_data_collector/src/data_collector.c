#include <netinet/in.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <time.h>
#include "data_collector.h"

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


void close_hdf5_handles(const raw_data_t *df) {
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
        return -1; // FIXME set to unique value representing error
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
        return -2; // FIXME set to unique value representing error
    }
    /**/
    const hsize_t iq_memspace_dim[2] = {1024, 1};
    const hsize_t misc_memspace_dim[1] = {1};
    hid_t i_mspace = H5Screate_simple(2, iq_memspace_dim, NULL);
    hid_t q_mspace = H5Screate_simple(2, iq_memspace_dim, NULL);
    hid_t ts_mspace = H5Screate_simple(1, misc_memspace_dim, NULL);
    hid_t pktidx_mspace = H5Screate_simple(1, misc_memspace_dim, NULL);

    int adc_i[ARRAY_SIZE];
    int adc_q[ARRAY_SIZE];

    int counter[1] = {0};
    double time[1] = {0.0};

    // TODO: I want to make this loop interruptible and infinite for use with multi-processing
    for(hsize_t current_samp = 0; current_samp < 3; current_samp++){
        iqdata_t data;
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

        const ssize_t bytes_received = recv(sock_fd, data.data, BUFFER_SIZE, MSG_WAITALL);
        if (bytes_received < 0) {
            perror("recv");
            return -3;
        }
        if (bytes_received != BUFFER_SIZE) {
            // DID NOT RECEIVE EXPECTED QUANTITY OF DATA
            return -4;
        }

        for (size_t i = 0; i < BUFFER_SIZE/4; i++) {
            data.data_uint[i] = htonl(data.data_uint[i]);
        }
        for (size_t i = 0; i < 1024; i++) {
            adc_i[i] = data.data_int[2*i];
            adc_q[i] = data.data_int[2*i+1];
        }

        // printf("First few are [%d, %d, %d]\n", adc_i_buff[0], adc_i_buff[1], adc_i_buff[2]);
        // Write the data
        H5Dwrite(df.i.dataset, df.i.datatype, i_mspace, df.i.dataspace, H5P_DEFAULT, adc_i );
        H5Dwrite(df.q.dataset, df.q.datatype, q_mspace, df.q.dataspace, H5P_DEFAULT, adc_q );
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


#ifndef __BUILD_FOR_LIB__
int main(int argc, char**argv){
    const int status = c_collect_data("test_dataset.h5");
    printf("c_collect_data returned %d\n", status);

    return 0;
}
#endif
