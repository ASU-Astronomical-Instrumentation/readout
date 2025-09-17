import kidpy3
import numpy as np
import logging
import time


log = logging.getLogger("test_makewave.py." + __name__)
log.setLevel(logging.DEBUG)  # Set the logging level

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# Create formatter and add to the handler
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)

# Add the handler to the logger
log.addHandler(console_handler)


def main_func():
    log.info("Create obj")
    dev = kidpy3.RFSOC("devrfsoc.yml")

    dev.rf1.chanmask = np.zeros(1)
    dev.rf2.chanmask = np.zeros(1)

    dev.rf1.raw_filename = "/home/carobers/workspace/readout/data/2power15_newtones_collection2.hdf5"
    # dev.rf2.raw_filename = "/home/carobers/workspace/readout/data/datB.hdf5"
    kidpy3.capture([dev.rf1], time.sleep, 30)
    log.info("main_func finished")

if __name__ == "__main__":

    main_func()
