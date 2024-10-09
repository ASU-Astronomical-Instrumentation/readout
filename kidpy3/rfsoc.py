"""
@authors
    - Cody Roberson <carobers@asu.edu>
@date 20241009

Information
-----------

The RFSOC class is the interface between the user's program and the operation of the readout system. The RFSOC class
reads a user configured yml file based on the included rfsoc_config_default.yml.
"""
import numpy as np
import logging
from uuid import uuid4
import redis
import json
import ipaddress
from omegaconf import OmegaConf

__all__ = [
    'RFSOC',
    'rfchannel'
]

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

        :return: true if connected, false if not
        :rtype: bool
        """
        is_connected = False
        try:
            self.r.ping()  # Doesn't just return t/f, it throws an exception if it can't connect
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

    def issue_command(self, rfsocname, command, args, timeout):
        """Issues a command via redis to the RFSoC and waits for a response or timeout.

        Args:
            rfsocname (str): The name of the RFSoC.
            command (str): The command to be issued.
            args (dict): The arguments for the command.
            timeout (int): The timeout period in seconds.
        Returns:
            The response data if the command is successful, None otherwise.
        """

        if not self.is_connected():
            log.error("NOT CONNECTED TO REDIS SERVER")
            return

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
            log.warning(
                "received no response from RFSOC within specified timeout period"
            )
            return None
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
            elif response["type"] == "subscribe":
                log.warning(f"received subscribe message\n{response}")

        except KeyError:
            err = "missing data from reply message"
            log.error(err)
            return

        except json.JSONDecodeError:
            err = "json failed to decode the body of the reply message"
            log.error(err)
            return


class RFSOC:
    def __init__(self, yaml_cfg: str ) -> None:
        """This is the key interface between the User's commands and the responding RFSOC system.
        """

        # First, we pull in our config and assign it to variables
        try:
            self.config = OmegaConf.load(yaml_cfg).rfsoc_config
            rfsoc_name = self.config.rfsoc_name
            redis_ip = self.config.redis_ip
            redis_port = int(self.config.redis_port)
            bitstream = self.config.bitstream
        except FileNotFoundError:
            log.error("Config file not found, this is required for operation.")
        except OmegaConf.ConfigAttributeError as e:
            log.error(f"Expected a parameter to be present in the config file however, it was not found."
                      f"Is it missing or is there a typo?")
            raise e

        log.debug(f"rfsoc object created {rfsoc_name} {redis_ip}")
        self.name = rfsoc_name
        self._ch1 = rfchannel()
        self._ch2 = rfchannel()

        self.rcon = RedisConnection(redis_ip, redis_port)

        # Next we'll upload a bitstream
        self.__upload_bitstream(bitstream)

        # Finally, we'll configure the hardware
        self.__config_hardware()

    def __upload_bitstream(self, path: str):
        """Command the RFSoC to upload(or reupload) it's FPGA Firmware"""
        assert isinstance(path, str) == True, "Path should be a string"
        args = {"abs_bitstream_path": path}
        response = self.rcon.issue_command(self.name, "upload_bitstream", args, 20)
        if response is None:
            log.error("upload_bitstream failed")
            return
        log.info("upload_bitstream success")
        return

    def __config_hardware(self) -> bool:
        """
        Configure the network parameters on the RFSOC
        :param data_a_srcip: Source IP for data A (channel 1)
        :type data_a_srcip: str
            ex: "192.168.3.40"
        :param data_b_srcip: Source IP for data B (channel 2)
        :param data_a_dstip: Desintation IP for data A (channel 1)
        :param data_b_dstip: Desintation IP for data B (channel 2)
        :param dstmac_a: Destination MAC address data A (channel 1)
        :param dstmac_b: Destination MAC address data B (channel 2)
        :param port_a: Data A (channel 1) port
            Note: this is used as both source and destination ports
        :param port_b: Data B (channel 2) port
            Note: this is used as both source and destination ports
        :return:
        """
        eth = self.config.ethernet_config
        data = {}
        data["data_a_srcip"] = eth.udp_data_a_sourceip
        data["data_a_dstip"] = eth.udp_data_a_destip
        data["data_b_dstip"] = eth.udp_data_b_sourceip
        data["data_b_srcip"] = eth.udp_data_b_destip
        data["destmac_a_msb"] = eth.destmac_a[:8]
        data["destmac_a_lsb"] = eth.destmac_a[8:]
        data["destmac_b_msb"] = eth.destmac_b[:8]
        data["destmac_b_lsb"] = eth.destmac_b[8:]
        data["port_a"] = eth.port_a
        data["port_b"] = eth.port_b

        response = self.rcon.issue_command(self.name, "config_hardware", data, 10)
        if response is None:
            log.error("config_hardware failed")
            return False
        log.info("config_hardware success")
        self._ch1.port = eth.port_a
        self._ch2.port = eth.port_b
        return True

    def set_tone_list(self, chan=1, tonelist=[], amplitudes=[]):
        """Set a DAC channel to generate a signal from a list of tones

        :param chan: The DAC channel on the RFSoC to set, defaults to 1
        :type chan: int, optional
        :param tonelist: list of tones in MHz to generate, defaults to []
        :type tonelist: list, optional
        :param amplitudes: list of tone powers per tone, Normalized to 1, defaults to []
        :type amplitudes: list, optional
        """

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
            self._ch1.baseband_freqs = f
            self._ch1.tone_powers = a
            self._ch1.n_tones = len(f)

        elif chan == 2:
            self._ch2.baseband_freqs = f
            self._ch2.tone_powers = a
            self._ch2.n_tones = len(f)
        else:
            log.error(f"Invalid channel number {chan}")
            return

        response = self.rcon.issue_command(self.name, "set_tone_list", data, 10)
        if response is None:
            log.error("set_tone_list failed")
            return

    def get_tone_list(self, chan: int = 1):
        """
        Retrieves the tone list and amplitudes for the specified channel.
        Note that this function does update the internal state of the rfchannel object. This is to ensure that the
        tones and amplitudes are in sync with the HDF5 data files.

        Args:
            chan (int): The channel number. Defaults to 1.

        Returns:
            tuple: A tuple containing the baseband frequencies and tone powers.


        """
        data = {"channel": chan}
        response = self.rcon.issue_command(self.name, "get_tone_list", data, 10)
        if response is None:
            log.error("get_tone_list failed")
        else:
            if chan == 1:
                self._ch1.baseband_freqs = response["tone_list"]
                self._ch1.tone_powers = response["amplitudes"]
                self._ch1.n_tones = len(response["tone_list"])
            else:
                self._ch2.baseband_freqs = response["tone_list"]
                self._ch2.tone_powers = response["amplitudes"]
                self._ch2.n_tones = len(response["tone_list"])

            log.info(f"get_tone_list success for channel {chan}")
            return self._ch1.baseband_freqs, self._ch1.tone_powers


class rfchannel:
    def __init__(self) -> None:
        """
        Contains the state information relevant to an data collection event.
        The information used here is pulled into the DataRawDataFile

        :param str raw_filename: path to where the HDF5 file shall exist.
        :param str ip: ip address of UDP stream to listen to
        :param int port: port of UDP to listen to, default is 4096
        :param str name: Friendly Name to call the channel. This is relevant to logs, etc
        :param int n_sample: n_samples to take. While this is used to format the
            rawDataFile, it should be
            left as 0 for now since udp2.capture() dynamically resizes/allocates it's datasets.
        :param int n_resonator: Number of resonators we're interested in / Tones we're generating
            from the RFSOC dac mapped to this Channel.
        :param int n_attenuator: Dimension N Attenuators
        :param np.ndarray baseband_freqs: array of N resonator tones
        :param np.ndarray attenuator_settings: Array of N Attenuator settings
        :param int sample_rate: Data downlink sample rate ~488 Samples/Second
        :param int tile_number: Which tile this rf channel belongs to
        :param int rfsoc_number: Which rfsoc unit is used
        :param int chan_number: channel # of the rfsoc being used
        :param int ifslice_number: Which IF slice the rfsoc channel # is using.
        :param str lo_sweep_filename: path to the LO sweep data with which to append to the rawDataFile.

        """

        self.raw_filename = ""
        self.ip = ""  # udop datastream IP address.
        self.baseband_freqs = np.empty(2)  # empty ndarray
        self.tone_powers = np.empty(2)
        self.attenuator_settings = (0.0, 0.0)
        self.n_tones = 0

        self.port = 4096
        self.name = ""
        self.n_sample = 488
        self.n_attenuators = 2
        self.sample_rate = 488
        self.tile_number = 0
        self.rfsoc_number = 0
        self.chan_number = 0
        self.ifslice_number = 0
        self.lo_sweep_filename = ""
        self.n_fftbins = 1024
        self.lo_freq = 400.0
