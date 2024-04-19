"""
@author: Cody Roberson
@date: Apr 2024
@file: redisControl.py
@description:
    This file is the main control loop for the rfsoc. It listens for commands from the redis server and executes them.
    I use a dictionary to map commands to functions. Apparently, this is called a "dispatch table".
    I just want to go back to C and use a switch statement :c.


"""

# Set up logging
import logging

__LOGFMT = "%(asctime)s|%(levelname)s|%(filename)s|%(lineno)d|%(funcName)s| %(message)s"
logging.basicConfig(format=__LOGFMT, level=logging.DEBUG)
log = logging.getLogger(__name__)
logh = logging.FileHandler("./rediscontrol_debug.log")
log.addHandler(logh)
logh.setFormatter(logging.Formatter(__LOGFMT))


# rfsocInterface uses the 'PYNQ' library which requires root priviliges+
# FIXME uncomment when done testing
# import getpass
# if getpass.getuser() != "root":
#     print("rfsocInterface.py: root priviliges are required, please run as root.")
#     exit()


import redis

# import rfsocInterface
from uuid import uuid4
import numpy as np
import json
from time import sleep
import config

import rfsocInterfaceDual as ri

last_tonelist_chan1 = []
last_tonelist_chan2 = []

def create_response(status, error, data):
    pass

def config_hardware(data: dict):
    try:
        srcip = data["dataA_srcip"]
        dstip = data["dataB_srcip"]
        macmsb = data["destmac_MSB"]
        maclsb = data["destmac_LSB"]
        macmsb = int(macmsb, 32)
        maclsb = int(maclsb, 16)
        ri.configure_registers(srcip, dstip, macmsb, maclsb)
    except KeyError:
        err = "missing required parameters"
        log.error(err)
        return (False, err, "")
    except ValueError:
        err = "invalid parameter data type"
        log.error(err)
        return (False, err, "")
    else:
        return (True, "", "")

def upload_bitstream(data: dict):
    try:
        bitstream = data["bitstream"]
        ri.uploadOverlay(bitstream)
    except KeyError:
        err = "missing required parameters"
        log.error(err)
        return (False, err, "")
    return (True, "", "")

def set_tone_list(data: dict):
    try:
        strtonelist = data["tone_list"]
        chan = int(data["channel"])
        tonelist = np.array(strtonelist)
        x, phi, freqactual = ri.generate_wave_ddr4(tonelist)
        ri.load_bin_list(chan, freqactual)
        wave_r, wave_i = ri.norm_wave(x)
        ri.load_ddr4(chan, wave_r, wave_i, phi)
        ri.reset_accum_and_sync(chan, freqactual)
    except KeyError: # tone_list does not exist
        err = "missing required parameters"
        log.error(err)
        return (False, err, "")
    except ValueError:
        err = "invalid parameter data type"
        log.error(err)
        return (False, err)
    return (True, "", "")

def get_tone_list(data: dict):
    global last_tonelist
    try:
        chan = int(data["channel"])
        if chan == 1:
            return (True, "", last_tonelist_chan1)
        elif chan == 2:
            return (True, "", last_tonelist_chan2)
        else:
            return (False, "Bad channel number", "")
    except KeyError:
        err = "missing required parameters"
        log.error(err)
        return (False, err, "")
    except ValueError:
        err = "invalid parameter data type"
        log.error(err)
        return (False, err, "")



def load_config() -> config.GeneralConfig:
    """Grab config from a file or make it if it doesn't exist."""
    c = config.GeneralConfig("rfsoc_config.cfg")
    c.write_config()
    return c


def main():
    conf = load_config()
    conf.cfg.rfsocName = "rfsoc1"
    crash_on_noconnection = False
    connection = RedisConnection(conf.cfg.redis_host, port=conf.cfg.redis_port)

    #loop forever until connection comes up?
    while 1:
        msg = connection.grab_command_msg()
        if msg['type'] == "message":
            try:
                command = json.loads(msg["data"].decode())
            except json.JSONDecodeError:
                log.error(f"Could not decode JSON from command: {command['command']}")
                continue
            
            if command["command"] in COMMAND_DICT:
                function = COMMAND_DICT[command["command"]]
                args = {}
                try:
                    args = command["data"] 
                except KeyError:
                    log.warning(f"No data provided for command: {command['command']}")
                    continue
                function(args)
            else:
                log.warning(f"Unknown command: {command['command']}")


class RedisConnection:
    def __init__(self, host, port) -> None:
        self.r = redis.Redis(host=host, port=6379)

        if self.is_connected():
            self.pubsub = self.r.pubsub()
            self.pubsub.subscribe("COMMAND")

    def is_connected(self):
        """Check if the RFSOC is connected to the redis server

        :return: true if connected, false if not
        :rtype: bool
        """
        is_connected = False
        try:
            self.r.ping()  # Doesn't just return t/f, it throws an exception if it can't connect.. y tho?
            is_connected = True
            log.debug(f"Redis Connection Status: {is_connected}")
        except redis.ConnectionError:
            is_connected = False
            log.error("Redis Connection Error")
        except redis.TimeoutError:
            is_connected = False
            log.error("Redis Connection Timeout")
        finally:
            return is_connected

    def grab_command_msg(self):
        """Wait (indefinitely) for a message from the redis server

        :return: the message
        :rtype: str
        """
        if self.is_connected():
            self.pubsub.get_message(timeout=None)
            return 


COMMAND_DICT = {
    "config_hardware": config_hardware,
    "upload_bitstream": upload_bitstream,
    "set_tone_list": set_tone_list,
    "get_tone_list": get_tone_list,
}

if __name__ == "__main__":
    load_config()
