import kidpy3
import numpy as np
import logging
import time

from tqdm import tqdm

def dowait(seconds):
    import time
    from tqdm import tqdm
    for _ in tqdm(range(0, seconds)):
        time.sleep(1)

def main_func():
    dev = kidpy3.RFSOC("readout.yml")

    dev.rf1.chanmask = np.zeros(1)
    dev.rf2.chanmask = np.zeros(1)

    dev.rf1.raw_filename = "new_cdatacap.h5"
    # dev.rf2.raw_filename = "/home/carobers/workspace/readout/data/datB.hdf5"
    kidpy3.capture([dev.rf1], dowait, 400)

if __name__ == "__main__":

    main_func()
