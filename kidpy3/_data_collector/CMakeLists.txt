cmake_minimum_required(VERSION 4.0)
project(_data_collector C)

set(CMAKE_C_STANDARD 11)
INCLUDE_DIRECTORIES("/home/carobers/workspace/readout/kidpy3/lib/include")

add_executable(_data_collector src/_data_collector.c)
target_link_libraries(_data_collector PUBLIC "/home/carobers/workspace/readout/kidpy3/lib/libhdf5.so")