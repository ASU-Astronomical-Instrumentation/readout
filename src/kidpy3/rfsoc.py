"""
@authors
    - Cody Roberson <carobers@asu.edu>
@date 20241009

Information
-----------

The RFSOC class is the interface between the user's program and the operation of the readout system. The RFSOC class
reads a user configured yml file based on the included rfsoc_config_default.yml.
"""

from typing import Any

import numpy as np
import logging
from uuid import uuid4
import redis
import json
import os
from omegaconf import OmegaConf, omegaconf
from import ConfigKeyError, ConfigAttributeError
from .kp3Exceptions import *

from .data_handler import Rfchan

__all__ = ["RFSOC", "new_config"]

log = logging.getLogger(__name__)


class RedisConnection:
    """Class representing a connection to a Redis server.

    This class provides methods to check if the RFSoC is connected to the Redis server,
    issue commands via Redis to the RFSoC, and handle the responses.

    Attributes:
        r (redis.Redis): The Redis client instance.
        pubsub (redis.client.PubSub): The Redis pubsub instance.

    """

    def __init__(self, host, port) -> None:
        self.r = redis.Redis(host=host, port=port)

        if self.is_connected():
            self.pubsub = self.r.pubsub()
            self.pubsub.subscribe("REPLY")
            log.debug(self.pubsub.get_message(timeout=1))

    def is_connected(self):
        """Check if the RFSOC is connected to the redis server

        Returns:
            True if connected, false if not
        """
        is_connected = False
        try:
            self.r.ping()  # Doesn't just return t/f, it throws an exception if it can't connect
            is_connected = True
            log.debug(f"Redis Connection Status: {is_connected}")
        except redis.ConnectionError:
            log.error("Redis Connection Error")
        except redis.TimeoutError:
            log.error("Redis Connection Timeout")
        finally:
            return is_connected

    def issue_command(self, rfsocname, command, args, timeout):
        """Issues a command via redis to the RFSoC and waits for a response or timeout.

        Args:
            rfsocname (str): The name of the RFSoC.
            command (str): The command to be issued.
            args (dict): The arguments for the command.
            timeout (int): The timeout period in seconds.
        Returns:
            The response data if the command is successful, raises an exception otherwise.

        """

        if not self.is_connected():
            raise RedisConnectionError("RFSoC not connected")
        uuid = str(uuid4())
        cmddict = {
            "command": command,
            "uuid": uuid,
            "data": args,
        }

        log.debug(
            f"Issuing command payload {cmddict} with timeout {timeout}; uuid: {uuid}"
        )
        cmdstr = json.dumps(cmddict)
        self.r.publish(rfsocname, cmdstr)
        response = self.pubsub.get_message(timeout=timeout)
        if response is None:
            raise CommandTimeoutError
        # see command reference format in docs
        try:
            if response["type"] == "message":
                body = response["data"]
                body = json.loads(body.decode())
                status = body["status"]
                error = body["error"]
                reply_uuid = body["uuid"]
                data = body["data"]
                if reply_uuid != uuid:
                    # TODO: This can apparently just 'happen' idk if this should be improved or removed
                    log.warning(
                        f"reply UUID did not match message uuid as expected\nreplyuuid={reply_uuid}, uuid={uuid}"
                    )
                    return None
                if status == "OK":
                    log.info("Command Success")
                    return data
                else:
                    log.error(f" {rfsocname} reported an error:\n{error}")
                    return None
            elif (
                response["type"] == "subscribe"
            ):  # FIXME: This may consume a command but not handle the reply
                log.warning(f"received subscribe message\n{response}")

        except KeyError:
            err = "missing data from reply message"
            log.error(err)
            return

        except json.JSONDecodeError:
            err = "json failed to decode the body of the reply message"
            log.error(err)
            return


def new_config(as_dict: bool = False) -> omegaconf.DictConfig | dict[str, Any]:
    """
    Creates a new RFSOC Configuration object for the user to fill in. This is the main template for current
    and future changes to the system configuration. Although the RFSOC class requires an omegaconf object,
    it makes sense to support a dict as well since it's easy enough to handle.

    :param bool as_dict: (Optional.) If True, return a dict instead of an omegaconf object.
    :return: The omegaconf object or dictionary as specified by as_dict.
    """
    c = {
        "rfsoc_config": {
            "ethernet_config": {
                "udp_data_a_sourceip": "0.0.0.0",
                "udp_data_b_sourceip": "0.0.0.0",
                "udp_data_a_destip": "0.0.0.0",
                "udp_data_b_destip": "0.0.0.0",
                "destmac_a": "AABBCCDDEEFF",
                "destmac_b": "AABBCCDDEEFF",
                "port_a": 4096,
                "port_b": 4096,
            },
            "rfsoc_name": "MATCH_ME_TO_THE_RFSOC",
            "redis_ip": "127.0.0.1",
            "redis_port": 6379,
            "bitstream": "/remote/path/to/bitstream.bit",
        },
        "rf1": {
            "raw_filename": "",
        },
        "rf2": {
            "raw_filename": "",
        },
    }
    if as_dict:
        return c
    # Otherwise give us an omegaconf object.
    return OmegaConf.create(c)


class RFSOC:
    def __init__(self, configuration: str | dict[str, Any] | omegaconf.DictConfig):
        """This is the key interface between the User's commands and the responding RFSOC system.
        Should the user not have a configuration setup, they should use kidpy3.new_config() to generate
        one. After modifying it, they can use it here.

        Args:
            configuration (str | dict[str, Any] | omegaconf.DictConfig): The configuration of the RFSoC.
                This can be a path, omegaconf obj, or a dict.
        Raises:
            RedisConnectionError: If a failure to connect to the Redis server occurs.
            MissingConfigError: When attempting to grab config from the void.
            ConfigFileNotFound: When attempting to grab a config file from the void.
        """
        self.rf1 = Rfchan()
        self.rf2 = Rfchan()
        self.read_config(configuration)
        self.rcon = RedisConnection(self.redisip, self.redisport)

        # TODO: create a function that checks if the rfsoc on the other side exists and is on listening

    def read_config(self, config: str | dict[str, Any] | omegaconf.DictConfig) -> None:
        """
        Reads the RFSOC configuration from a file or a dictionary depending on whether
        it is a path, omegaconf object, or a dictionary. This function is called when an
        RFSOC object is created.

        Args:
            config (str | dict[str, Any] | omegaconf.DictConfig): The configuration to read.
                This can be a path, omegaconf obj, or a dict.
        Raises:
            MissingConfigError: When attempting to grab config from the void.
            ConfigFileNotFound: When attempting to grab a config file from the void.
        """
        if isinstance(config, str):
            if os.path.exists(config):
                self.cfg = OmegaConf.load(config)
            else:
                raise ConfigFileNotFound
        elif isinstance(config, dict):
            self.cfg = OmegaConf.create(config)
        elif isinstance(config, omegaconf.DictConfig):
            self.cfg = config

        try:
            self.name = self.cfg.rfsoc_config.rfsoc_name
            self.eth = self.cfg.rfsoc_config.ethernet_config
            self.rf1.ip = self.eth.udp_data_a_destip
            self.rf2.ip = self.eth.udp_data_b_destip
            self.rf1.port = self.eth.port_a
            self.rf2.port = self.eth.port_b
            self.redisip = self.cfg.rfsoc_config.redis_ip
            self.redisport = self.cfg.rfsoc_config.redis_port
            self.bitstream = self.cfg.rfsoc_config.bitstream

        except ConfigAttributeError as err:
            raise MissingConfigError(
                f"Expected '{err.full_key}' to exist in the specified config"
            ) from err

    def upload_bitstream(self, remote_path: str = ""):
        """Command the RFSoC to upload (or re-upload) it's FPGA Firmware

        Args:
            remote_path (str, optional): Remote path to bitstream file on device.
            This should be an absolute path.

        Raises:
            RedisConnectionError: If a failure to connect to the Redis server occurs.
            CommandTimeoutError: The command timed out.
        """
        if remote_path == "":
            args = {"abs_bitstream_path": self.bitstream}
        else:
            args = {"abs_bitstream_path": remote_path}

        _ = self.rcon.issue_command(self.name, "upload_bitstream", args, 21)
        log.info("upload_bitstream success")
        return True

    def config_hardware(self) -> bool:
        """
        Configure the network parameters on the RFSOC. These parameters are sources from the YAML
        file provided by the user when the RFSOC object is initialized.

        Raises:
            RedisConnectionError: If a failure to connect to the Redis server occurs.
            CommandTimeoutError: The command timed out.
            MissingConfigError: Attempted to read a parameter that is missing from the config.
        """
        data = {}
        try:
            data["data_a_srcip"] = self.eth.udp_data_a_sourceip
            data["data_a_dstip"] = self.eth.udp_data_a_destip
            data["data_b_dstip"] = self.eth.udp_data_b_destip
            data["data_b_srcip"] = self.eth.udp_data_b_sourceip
            data["destmac_a_msb"] = self.eth.destmac_a[:8]
            data["destmac_a_lsb"] = self.eth.destmac_a[8:]
            data["destmac_b_msb"] = self.eth.destmac_b[:8]
            data["destmac_b_lsb"] = self.eth.destmac_b[8:]
            data["port_a"] = self.eth.port_a
            data["port_b"] = self.eth.port_b

        except ConfigAttributeError as err:
            raise MissingConfigError(
                f"Expected '{err.full_key}' to exist in the specified config"
            ) from err

        _ = self.rcon.issue_command(self.name, "config_hardware", data, 10)

        log.info("config_hardware success")
        return True

    def set_tone_list(self, chan=1, tonelist=[], amplitudes=[]):
        """Set a DAC channel to generate a signal from a list of tones

        Arguments:
            chan(int): The DAC channel on the RFSoC to set.
                Channel 1 is for Dac0 (I), Dac1 (Q)
                Channel 2 is for Dac2 (I), Dac3 (Q)
            tonelist(list | npt.ndarray): list of tones in MHz to generate, defaults to []
            amplitudes(list | npt.ndarray): list of tone powers per tone, Normalized to 1, defaults to []

        Returns:
            bool on success

        Raises:
            RedisConnectionError: If a failure to connect to the Redis server occurs.
            CommandTimeoutError: The command timed out.
        """
        assert chan == 1 or chan == 2, "Expected either channel 1 or channel 2"
        assert len(tonelist) > 0, "Expected a list of at least 1 frequency"
        assert len(amplitudes) == len(
            tonelist
        ), "Expected the amplitude list to have the same length as the tone list"
        f = tonelist
        a = amplitudes
        data = {}
        # Convert numpy arrays to list as needed
        if isinstance(tonelist, np.ndarray):
            f = tonelist.tolist()
        if isinstance(amplitudes, np.ndarray):
            a = amplitudes.tolist()

        data["tone_list"] = f
        data["channel"] = chan
        data["amplitudes"] = a

        if chan == 1:
            self.rf1.baseband_freqs = f
            self.rf1.tone_powers = a
            self.rf1.n_tones = len(f)

        else:
            self.rf2.baseband_freqs = f
            self.rf2.tone_powers = a
            self.rf2.n_tones = len(f)

        _ = self.rcon.issue_command(self.name, "set_tone_list", data, 10)
        return True # If this had failed, there would be an exception so we can safely return true here.

    def get_tone_list(self, chan: int = 1) -> tuple[np.ndarray, np.ndarray]:
        """
        Retrieves the tone list and amplitudes for the specified channel.
        Note that this function does update the internal state of the rfchannel object. This is to ensure that the
        tones and amplitudes are in sync with the HDF5 data files.

        Args:
            chan (int): The DAC channel on the RFSoC to set. 1 or 2
                Channel 1 is for Dac0 (I), Dac1 (Q)
                Channel 2 is for Dac2 (I), Dac3 (Q)
        Returns:
            A tuple in the form ([Frequency List], [Amplitude List]) as numpy arrays

        Raises:
            RedisConnectionError: If a failure to connect to the Redis server occurs.
            CommandTimeoutError: The command timed out.
        """
        data = {"channel": chan}
        response = self.rcon.issue_command(self.name, "get_tone_list", data, 10)
        if response is None:
            log.error("get_tone_list failed")

        else:
            if chan == 1:
                self.rf1.baseband_freqs = response["tone_list"]
                self.rf1.tone_powers = response["amplitudes"]
                self.rf1.n_tones = len(response["tone_list"])
                return np.array(self.rf1.baseband_freqs), np.array(self.rf1.tone_powers)

            else:
                self.rf2.baseband_freqs = response["tone_list"]
                self.rf2.tone_powers = response["amplitudes"]
                self.rf2.n_tones = len(response["tone_list"])
                return np.array(self.rf2.baseband_freqs), np.array(self.rf2.tone_powers)

        return (np.array([0]), np.array([0]))
