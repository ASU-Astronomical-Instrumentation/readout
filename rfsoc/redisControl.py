"""
@author: Cody Roberson
@date: Feb 2024
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


def config_hardware(data: dict):
    srcip = ""
    dstip = ""
    mac = ""
    try:
        srcip = data["srcip"]
        dstip = data["dstip"]
        mac = data["mac"]
    
    except KeyError:
        log.error("config_hardware: missing required parameters")
        return

def upload_bitstream(data: dict):
    try:
        bitstream = data["bitstream"]
    except KeyError:
        log.error("upload_bitstream: missing required parameters")
        return

def set_tone_list(data: dict):
    pass

def get_tone_list(data: dict):
    pass

def set_amplitude_list(data: dict):
    pass

def get_amplitude_list(data: dict):
    pass



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
        if msg[type] == "message":
            command = json.loads(msg["data"])
            if command["command"] in COMMAND_DICT:
                function = COMMAND_DICT[command["command"]]
                args = {}
                try:
                    args = json.loads(command["data"])
                except json.JSONDecodeError:
                    log.error(f"Could not decode JSON from command: {command['command']}")
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
            return self.pubsub.get_message(timeout=None)


COMMAND_DICT = {
    "config_hardware": config_hardware,
    "upload_bitstream": upload_bitstream,
    "set_tone_list": set_tone_list,
    "get_tone_list": get_tone_list,
    "set_amplitude_list": set_amplitude_list,
    "get_amplitude_list": get_amplitude_list,
}

if __name__ == "__main__":
    load_config()
