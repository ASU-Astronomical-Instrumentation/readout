import kidpy3
import cProfile
filepath = "test_dataset.h5"
ip = "192.168.3.40"
port = 4096


# import os
# os.system(f"/usr/local/hdf5/bin/h5dump {filepath} > h5dump.txt")

kidpy3.udp2.capture(filepath, ip, port)
