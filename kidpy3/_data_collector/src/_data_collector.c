#include <netinet/in.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <time.h>
#include "_data_collector.h"
#include <signal.h>

static volatile sig_atomic_t stop = 0;

void handle_sig(int sig) {
    stop = 1;
}
void c_say_hi(void) {
    printf("Hello from C!\n");
}
void close_hdf5_handles(const raw_data_t *df) {
    H5Sclose(df->i_mem_space);
    H5Sclose(df->q_mem_space);
    H5Sclose(df->ts_mem_space);
    H5Sclose(df->pkt_idx_mem_space);
    H5Sclose(df->n_sample_mem_space);
    H5Tclose(df->i.datatype);
    H5Dclose(df->i.dataset);

    H5Tclose(df->q.datatype);
    H5Dclose(df->q.dataset);

    H5Tclose(df->ts.datatype);
    H5Dclose(df->ts.dataset);

    H5Tclose(df->pkt_idx.datatype);
    H5Dclose(df->pkt_idx.dataset);

    H5Tclose(df->n_sample.datatype);
    H5Dclose(df->n_sample.dataset);

    H5Gclose(df->grp_tod);
    H5Gclose(df->grp_dimension);


    H5Fclose(df->file);
}

int c_collect_data(const char *filename, const char *ip_addr, const int port) {
    // This function is intended to be a child of a python interpreter. The parent needs to kill us gracefully.
    // NOTE: This might actually be bad if the caller also changes how signals behave.

    struct sigaction sa;
    sa.sa_handler = handle_sig;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;
    sigaction(SIGINT, &sa, NULL);
    sigaction(SIGTERM, &sa, NULL);
    sigaction(SIGQUIT, &sa, NULL);

    int sock_fd;
    struct sockaddr_in server_addr;
    herr_t status;
    raw_data_t df;

    // Configure/create socket
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = inet_addr(ip_addr);
    server_addr.sin_port = htons(port);

    if ((sock_fd = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
        return -5; // FIXME set to unique value representing error
    }

    // Open hdf5 file and gather its parameters/stats
    df.file = H5Fopen(filename, H5F_ACC_RDWR, H5P_DEFAULT);
    df.grp_tod = H5Gopen2(df.file, "time_ordered_data", H5P_DEFAULT);
    df.grp_dimension = H5Gopen2(df.file, "dimension", H5P_DEFAULT);

    df.n_sample.dataset = H5Dopen(df.grp_dimension, "n_sample", H5P_DEFAULT);
    df.n_sample.datatype = H5Dget_type(df.n_sample.dataset);
    df.n_sample.dataspace = H5Dget_space(df.n_sample.dataset);
    df.n_sample.rank = H5Sget_simple_extent_dims(df.n_sample.dataspace, df.n_sample.dim, df.n_sample.max_dim);

    df.i.dataset = H5Dopen(df.grp_tod, "adc_i", H5P_DEFAULT);
    df.i.datatype = H5Dget_type(df.i.dataset);
    df.i.dataspace = H5Dget_space(df.i.dataset);
    df.i.rank = H5Sget_simple_extent_dims(df.i.dataspace, df.i.dim, df.i.max_dim);

    df.q.dataset = H5Dopen(df.grp_tod, "adc_q", H5P_DEFAULT);
    df.q.datatype = H5Dget_type(df.q.dataset);
    df.q.dataspace = H5Dget_space(df.q.dataset);
    df.q.rank = H5Sget_simple_extent_dims(df.q.dataspace, df.q.dim, df.q.max_dim);

    df.ts.dataset = H5Dopen(df.grp_tod, "timestamp", H5P_DEFAULT);
    df.ts.datatype = H5Dget_type(df.ts.dataset);
    df.ts.dataspace = H5Dget_space(df.ts.dataset);
    df.ts.rank =
        H5Sget_simple_extent_dims(df.ts.dataspace, df.ts.dim, df.ts.max_dim);

    df.pkt_idx.dataset = H5Dopen(df.grp_tod, "pkt_idx", H5P_DEFAULT);
    df.pkt_idx.datatype = H5Dget_type(df.pkt_idx.dataset);
    df.pkt_idx.dataspace = H5Dget_space(df.pkt_idx.dataset);
    df.pkt_idx.rank = H5Sget_simple_extent_dims(
        df.pkt_idx.dataspace, df.pkt_idx.dim, df.pkt_idx.max_dim);



    struct timeval tv;
    tv.tv_sec = 1;
    tv.tv_usec = 0;
    if (setsockopt(sock_fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv)) < 0) {
        close(sock_fd);
        close_hdf5_handles(&df);
        return -4;

    }
    if (bind(sock_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        close(sock_fd);
        close_hdf5_handles(&df);
        return -3;
    }

    const hsize_t iq_memspace_dim[2] = {1024, 1};
    const hsize_t misc_memspace_dim[1] = {1};
    df.i_mem_space = H5Screate_simple(2, iq_memspace_dim, NULL);
    df.q_mem_space = H5Screate_simple(2, iq_memspace_dim, NULL);
    df.ts_mem_space = H5Screate_simple(1, misc_memspace_dim, NULL);
    df.pkt_idx_mem_space = H5Screate_simple(1, misc_memspace_dim, NULL);
    df.n_sample_mem_space = H5Screate_simple(1, misc_memspace_dim, NULL);

    int adc_i[ARRAY_SIZE];
    int adc_q[ARRAY_SIZE];

    uint32_t counter[1] = {0};
    uint32_t n_samp[1] = {1};
    double time[1] = {0.0};
    hsize_t current_samp = 0;

    while(!stop){

        iqdata_t data;
        const hsize_t curr_pos[] = {0, current_samp};
        const hsize_t curr_pos1d[] = {current_samp};

        // Use clock_gettime if available
        struct timespec ts;

        const ssize_t bytes_received = recv(sock_fd, data.data, BUFFER_SIZE, MSG_WAITALL);
        clock_gettime(CLOCK_REALTIME, &ts);
        time[0] = (double)ts.tv_sec + (double)ts.tv_nsec / 1.0e9;
        if (bytes_received < 0) {
            H5Fflush(df.file, H5F_SCOPE_LOCAL);
            close(sock_fd);
            close_hdf5_handles(&df);
            if (stop == 1) {
                /*We're much more likely to interrupt the socket while it waits than the rest of the
                program, which makes it falsely return an error since we interrupt a syscall*/
                return 0;
            }else {
                return -2;
            }
        }
        if (bytes_received != BUFFER_SIZE) {
            close(sock_fd);
            close_hdf5_handles(&df);
            return -1;
        }

        // for (size_t i = 0; i < BUFFER_SIZE/4; i++) {
        //     data.data_uint[i] = htonl(data.data_uint[i]);
        // }
        for (size_t i = 0; i < 1024; i++) {
            adc_i[i] = data.data_int[2*i];
            adc_q[i] = data.data_int[2*i+1];
        }
        data.data_uint[2049] = htonl(data.data_uint[2049]);
        counter[0] = data.data_uint[2049];


        // Extend the dataset
        df.i.dim[1] += 1;
        df.q.dim[1] += 1;
        df.ts.dim[0] += 1;
        df.pkt_idx.dim[0] += 1;

        status = H5Dset_extent(df.i.dataset, df.i.dim);
        if (status < 0) {
            close(sock_fd);
            close_hdf5_handles(&df);
            return -6;
        }
        status = H5Dset_extent(df.q.dataset, df.q.dim);
        if (status < 0) {
            close(sock_fd);
            close_hdf5_handles(&df);
            return -7;
        }
        status = H5Dset_extent(df.ts.dataset, df.ts.dim);
        if (status < 0) {
            close(sock_fd);
            close_hdf5_handles(&df);
            return -8;
        }
        status = H5Dset_extent(df.pkt_idx.dataset, df.ts.dim);
        if (status < 0) {
            close(sock_fd);
            close_hdf5_handles(&df);
            return -9;
        }


        //Need a better way to write these changes, maybe flush instead of close/reopen?
        H5Sclose(df.i.dataspace);
        H5Sclose(df.q.dataspace);
        H5Sclose(df.ts.dataspace);
        H5Sclose(df.pkt_idx.dataspace);


        df.i.dataspace = H5Dget_space(df.i.dataset);
        df.q.dataspace = H5Dget_space(df.q.dataset);
        df.ts.dataspace = H5Dget_space(df.ts.dataset);
        df.pkt_idx.dataspace = H5Dget_space(df.pkt_idx.dataset);

        H5Sselect_hyperslab(df.i.dataspace, H5S_SELECT_SET, curr_pos, NULL, iq_memspace_dim, NULL);
        H5Sselect_hyperslab(df.q.dataspace, H5S_SELECT_SET, curr_pos, NULL, iq_memspace_dim, NULL);
        H5Sselect_hyperslab(df.ts.dataspace, H5S_SELECT_SET, curr_pos1d, NULL, misc_memspace_dim, NULL);
        H5Sselect_hyperslab(df.pkt_idx.dataspace, H5S_SELECT_SET, curr_pos1d, NULL, misc_memspace_dim, NULL);

        // Write the data
        H5Dwrite(df.i.dataset, df.i.datatype, df.i_mem_space, df.i.dataspace, H5P_DEFAULT, adc_i );
        H5Dwrite(df.q.dataset, df.q.datatype, df.q_mem_space, df.q.dataspace, H5P_DEFAULT, adc_q );
        H5Dwrite(df.ts.dataset, df.ts.datatype, df.ts_mem_space, df.ts.dataspace, H5P_DEFAULT, time );
        H5Dwrite(df.pkt_idx.dataset, df.pkt_idx.datatype, df.pkt_idx_mem_space, df.pkt_idx.dataspace, H5P_DEFAULT, counter );
        H5Dwrite(df.n_sample.dataset, df.n_sample.datatype, df.n_sample_mem_space, df.n_sample.dataspace, H5P_DEFAULT, n_samp);

        current_samp += 1;
        n_samp[0] += 1;
    }
    close(sock_fd);
    close_hdf5_handles(&df);
    H5Fflush(df.file, H5F_SCOPE_LOCAL);
    
    return 0;
}


#ifndef __BUILD_FOR_LIB__
int main(int argc, char**argv){
    // if (argc != 2) {
    //     printf("Usage: %s <output_filename>\n", argv[0]);
    //     return -1;
    // }
    const char* file = "/home/carobers/workspace/readout/scratchpad/test_dataset.h5";
    // const int status = c_collect_data(argv[1], "192.168.3.40", 4096);
    const int status = c_collect_data(file, "192.168.3.40", 4096);
    return 0;
}
#endif
