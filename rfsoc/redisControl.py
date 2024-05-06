"""
@author: Cody Roberson
@date: Apr 2024
@file: redisControl.py
@description:
    This file is the main control loop for the rfsoc. It listens for commands from the redis server and executes them.
    A dictionary is used to map commands to functions in order to create a dispatch table".
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
import getpass

if getpass.getuser() != "root":
    print("rfsocInterface.py: root priviliges are required, please run as root.")
    exit()


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


def create_response(
    status: bool,
    uuid: str,
    data: dict = {},
    error: str = "",
):
    rdict = {
        "status": "OK" if status else "ERROR",
        "uuid": uuid,
        "error": error,
        "data": data,
    }
    response = json.dumps(rdict)
    return response


#################### Command Functions ###########################
def upload_bitstream(uuid, data: dict):
    status = False
    err = ""
    try:
        bitstream = data["abs_bitstream_path"]
        ri.uploadOverlay(bitstream)
        status = True
    except KeyError:
        err = "missing required parameters"
        log.error(err)
    return create_response(status, uuid, error=err)


def config_hardware(uuid, data: dict):
    status = False
    err = ""
    try:
        srcip = data["data_a_srcip"]
        dstip = data["data_b_srcip"]
        macmsb = data["destmac_msb"]
        maclsb = data["destmac_lsb"]
        macmsb = int(macmsb, 32)
        maclsb = int(maclsb, 16)
        ri.configure_registers(srcip, dstip, macmsb, maclsb)
        status = True
    except KeyError:
        err = "missing required parameters"
        log.error(err)
    except ValueError:
        err = "invalid parameter data type"
        log.error(err)
    return create_response(status, uuid, error=err)


def set_tone_list(uuid, data: dict):
    status = False,
    err = ""
    try:
        strtonelist = data["tone_list"]
        chan = int(data["channel"])
        amplutudes = data["amplitudes"]
        tonelist = np.array(strtonelist)
        x, phi, freqactual = ri.generate_wave_ddr4(tonelist)
        ri.load_bin_list(chan, freqactual)
        wave_r, wave_i = ri.norm_wave(x)
        ri.load_ddr4(chan, wave_r, wave_i, phi)
        ri.reset_accum_and_sync(chan, freqactual)
        status = True
    except KeyError:  # tone_list does not exist
        err = "missing required parameters"
        log.error(err)
    except ValueError:
        err = "invalid parameter data type"
        log.error(err)
    return create_response(status, uuid, error=err)


def get_tone_list(uuid, data: dict):
    global last_tonelist
    status = False,
    err = ""
    data = {}
    try:
        chan = int(data["channel"])
        data['channel'] = chan
        if chan == 1:
            data['tone_list'] = last_tonelist_chan1
            status = True
        elif chan == 2:
            data['tone_list'] = last_tonelist_chan2
            status = True
        else:
            err = "bad channel number"
            status = False
    except KeyError:
        err = "missing required parameters"
        log.error(err)
    except ValueError:
        err = "invalid parameter data type"
        log.error(err)

    return create_response(status, uuid, error=err, data = data)

############ end of command functions #############
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

    # loop forever until connection comes up?
    while 1:
        msg = connection.grab_command_msg()
        if msg["type"] == "message":
            try:
                command = json.loads(msg["data"].decode())
            except json.JSONDecodeError:
                log.error(f"Could not decode JSON from command: {command['command']}")
                continue
            except KeyError:
                log.error(f"no data field in command message")
                continue

            if command["command"] in COMMAND_DICT:
                function = COMMAND_DICT[command["command"]]
                args = {}
                uuid = "no uuid"
                try:
                    args = command["data"]
                    uuid = command['uuid']
                except KeyError:
                    log.warning(f"No data provided for command: {command['command']}")
                    # Should this actually reply with an error message
                    continue
                response_str = function(uuid, args)
                connection.sendmsg(response_str)
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

    def sendmsg(self, response):
        if self.is_connected():
            self.r.publish("REPLY", response)
            return


COMMAND_DICT = {
    "config_hardware": config_hardware,
    "upload_bitstream": upload_bitstream,
    "set_tone_list": set_tone_list,
    "get_tone_list": get_tone_list,
}

if __name__ == "__main__":
    load_config()
