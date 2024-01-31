import configparser
import sys, os

def create_config():
    config = configparser.ConfigParser()

    config["DEFAULT"] = {
        "rf1dchan1": "192.168.3.50",
        "rf1dchan2": "192.168.3.51",
        "rf1dstmac": "A0CEC8B0C852",
        "rf2dchan1": "192.168.3.52",
        "rf2dchan2": "192.168.3.53",
        "rf2dstmac": "A0CEC8B0C852",
        "rf3dchan1": "192.168.3.54",
        "rf3dchan2": "192.168.3.55",
        "rf3dstmac": "A0CEC8B0C852",
    }
    config.write(open("rfsoc_config.cfg", "w"))

def load_config():
    config = configparser.ConfigParser()
    config.read("rfsoc_config.cfg")
    return config