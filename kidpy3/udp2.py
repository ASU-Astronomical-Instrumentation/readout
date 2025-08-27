import _data_collector
from .data_handler import Rfchan
from .data_handler import RawDataFile
import numpy as np
import logging
import socket

RED = "\033[0;31m"
NC = "\033[0m"  # No Color
logger = logging.getLogger(__name__)
def capture(filename, ip, port):
    return _data_collector.collect_data(filename, ip, port)
# def capture(channels: list, fn=None, *args, **kwargs):
#     """
#
#     :param channels:
#     :param fn:
#     :param args:
#     :param kwargs:
#     :return:
#     """
#
#     # return _data_collector.collect_data(filename, ip, port)

def capture_packets(channel: Rfchan, n_packets: int):
    """
    Captures to memmory instead of to a file, returning the result.
    Usefull for developing functions like LO sweep
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
            soc.settimeout(1)
            data = soc.recv(8208 * 1)
            if len(data) < 8000:
                print("invalid packet recieved")
                return
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

    packets = np.zeros(shape=(2052, n_packets))

    for i in range(n_packets):
        data_2 = parse_packet()
        packets[:, i] = data_2
    soc.close()
    return packets

def hi():
    _data_collector.say_hello()