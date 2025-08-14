/**
 *
 * Interfaces with a linux system socket for the purposes of grabbing UDP data
 * from the RFSoC
 */
#include "data_collector.h"
void c_say_hi(void) { printf("Hello world!\n"); }

int get_packet(int socketfd, int out_array[ARRAY_SIZE]) {
  uint8_t buffer[BUFFER_SIZE];
  ssize_t bytes_received;

  bytes_received = recv(socketfd, buffer, BUFFER_SIZE, MSG_WAITALL);

  if (bytes_received < 0) {
    perror("recv");
    return -1;
  }
  if (bytes_received != BUFFER_SIZE) {
    // DID NOT RECEIVE EXPECTED QUANTITY OF DATA
    return -2;
  }
  memcpy(out_array, buffer, ARRAY_SIZE * sizeof(int32_t));

  // Optionally convert from network to host byte order
  for (int i = 0; i < ARRAY_SIZE; i++) {
    out_array[i] = ntohl(out_array[i]);
  }

  return 0;
}
int _capture_data(void) {
  int sockfd;
  struct sockaddr_in server_addr;

  // Create UDP socket
  if ((sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
    perror("socket");
    return -1;
  }

  memset(&server_addr, 0, sizeof(server_addr));
  server_addr.sin_family = AF_INET;
  server_addr.sin_addr.s_addr = inet_addr("192.168.3.40");
  server_addr.sin_port = htons(4096);

  if (bind(sockfd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
    perror("bind");
    close(sockfd);
    return -2;
  }

  // Buffer to store integers
  int32_t data[ARRAY_SIZE];

  // Receive and parse one packet
  if (get_packet(sockfd, data) == 0) {
    printf("Received %d integers:\n", ARRAY_SIZE);
  }

  close(sockfd);
  return 0;
}

#ifndef __BUILD_FOR_LIB__

int main(int argc, char **argv) {
  // Lets open an HDF file
  //
  const char *hdf_file = "./myfile.h5";
  hid_t file;
  hid_t dataspace, dataset, filespace, memspace;
  hid_t prop;

  printf("Attempting to open file path=%s\n", hdf_file);
}

#endif
