"""
This module contains the C implementation and cython wrapper for the data collector
previously implemented in python.
"""
import ipaddress
from libc.stdint cimport int16_t
import os
cdef extern from "src/_data_collector.h" nogil:
    void c_say_hi()
    int c_collect_data(const char *filename, const char *ip_addr, const int port)

def say_hello():
    c_say_hi()

def collect_data(filename: str, ip_addr: str, port: int) -> int:
    assert os.path.exists(filename), "File does not exist. This function requires a valid, already formatted HDF5 file."
    _ = ipaddress.IPv4Address(ip_addr) # check if it's a valid IPv4 address string

    cdef bytes b_filename = filename.encode("utf-8")
    cdef const char *c_str_filename = <char*>b_filename

    cdef bytes b_ipaddr = ip_addr.encode("utf-8")
    cdef const char *c_str_ip_addr = <char*>b_ipaddr

    cdef int16_t c_port = port & 0xFFFF
    cdef int result = c_collect_data(c_str_filename, c_str_ip_addr, c_port)
    if result == -1:
        raise OSError(f"[{result}] Did not receive the correct amount of bytes from the data stream")
    elif result == -2:
        raise OSError(f"[{result}] Socket error. Either it was interrupted or timed out.")
    elif result == -3:
        raise OSError(f"[{result}] Failed to bind the socket. The port is likely already in use.")
    elif result == -4:
        raise OSError(f"[{result}] Failed to set a timeout on the socket.")
    elif result == -5:
        raise OSError(f"[{result}] Failed to create/open the socket file descriptor.")
    elif -6 >= result >= -9:
        raise IOError(f"[{result}]"
                      f" Failed to extend the HDF5 Dataset")
    return result