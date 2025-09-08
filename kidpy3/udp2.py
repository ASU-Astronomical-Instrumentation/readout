from _data_collector import collect_data, say_hello
from .data_handler import get_last_lo
from .data_handler import Rfchan
from .data_handler import RawDataFile
import signal
import numpy as np
import logging
import multiprocessing as mproc
import socket
from typing import List
import os

logger = logging.getLogger(__name__)

def capture(channels: List[Rfchan], fn=None, *args, **kwargs):
    """
    Captures UDP streams to a data file.
    :param channels: List of RfChan objects which can be pulled from data_handler.py
    :param fn: Function to execute in the foreground while steaming data is recorded.
    :param args: Provide a list of arguments to be passed to the function.
    :param kwargs:
    :return:
    :raises ValueError:
    """
    if fn is None: raise ValueError("fn must be provided, otherwise nothing will happen." 
                                    "Hint: time.sleep(...) is sufficient if no fn is desired.")

    file_list = []
    for chan in channels: file_list.append(chan.raw_filename)
    if len(file_list) != len(set(file_list)):
        raise ValueError("Non unique raw filenames provided. "
            "We can't save data from multiple channels to the same file.")

    # Validate inputs
    if channels is None or len(channels) == 0:
        raise ValueError("channels must be a list of RfChan objects")

    process_list: List[mproc.Process] = []
    result = None

    # Ensure all sockets are openable and data is streaming. This will raise an exception if not.
    for chan in channels:
        logger.debug(f"Testing socket connection to {chan.ip}:{chan.port}")
        capture_packets(chan, 1)

    logger.debug("Creating and populating blank RawDataFiles and blank datasets for each channel")

    # Create and Populate blank RawDataFiles and blank datasets for each channel
    for chan in channels:
        rdf = RawDataFile(chan.raw_filename, 'w')
        rdf.format(chan.n_sample, chan.n_tones, chan.n_fftbins)
        rdf.set_global_data(chan)
        rdf.append_lo_sweep(get_last_lo(chan.tile_name))
        rdf.close()


    # Launch a subprocess for each channel. Call user provided function in the foreground.
    # Close out the processes when the user-provided function returns.
    logger.info("Launching data collection processes")
    with mproc.Manager() as manager:
        for chan in channels:
            new_process = mproc.Process(target=collect_data, args=(chan.raw_filename, chan.ip, chan.port))
            logger.debug(f"Starting data collection process for {chan.ip}")
            new_process.start()
            process_list.append(new_process)

        result = fn(*args, **kwargs)

        logger.info("User provided function finished. Signaling data collection processes to exit")
        for process in process_list:
            os.kill(process.pid, signal.SIGINT)
            process.join(timeout=2)
            logger.debug(
                f"Process {process.pid} joined with exit code {process.exitcode}"
            )
    return result


def capture_packets(channel: Rfchan, n_packets: int):
    """
    Captures to memory instead of to a file, returning the result.
    Useful for developing functions like LO sweep
    """
    log = logger.getChild(__name__)
    soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        soc.bind((channel.ip, channel.port))
    except socket.error:
        log.error(
            "Tried to bind to the socket but failed. It may already be in use or the address/port"
            + "in question is invalid. The ethernet port could otherwise be disconnected as well"
        )

    def parse_packet():
        try:
            soc.settimeout(2)
            data = soc.recv(8208 * 1)
            if len(data) < 8000:
                raise OSError("Received incomplete packet")
            datarray = bytearray(data)

            # now allow a shift of the bytes
            spec_data = np.frombuffer(datarray, dtype="<i")
            # offset allows a shift in the bytes
            return spec_data  # int32 data type
        except socket.timeout:
            log.error(
                "The socket timed out and we couldn't obtain data. There are a few diagnostics:"
                + "\n1. Is the FPGA programmed and generating tones?"
                + "\n2. Is the mac address for this channel correct?"
                + "\n3. In the OS, is an MTU of 9000 set for this ethernet interface?"
                + "\n4. Are both the Ip source and destination addresses correct?"
            )
            raise

    packets = np.zeros(shape=(2052, n_packets))

    for i in range(n_packets):
        data_2 = parse_packet()
        packets[:, i] = data_2
    soc.close()
    return packets

def hi():
    say_hello()


