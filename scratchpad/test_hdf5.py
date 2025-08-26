import kidpy3

filepath = "./scratchpad/test_dataset.h5"
ip = "127.0.0.1"
port = 4096

print("KIDPY3 CAPTURE RETURNED WITH A CODE OF ", kidpy3.udp2.capture(filepath, ip, port))
# import os
# os.system(f"/usr/local/hdf5/bin/h5dump {filepath} > h5dump.txt")