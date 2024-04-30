import numpy as np
import logging
from uuid import uuid4
import redis

log = logging.getLogger(__name__)

"""
Note to self, there should only be one common redis connection between different instances of rfsoc and therefore
rfsoc should NOT initialize the variable and instead be made module intrinsic..........
"""

HOST = "localhost"

__all__ = ["RFSOC", "rfchannel", "RedisConnection"]

rserv = RedisConnection(HOST)


def _create_cmdstr(command:str, args:dict):
    
    return cmddict


class RFSOC:
    rcon = RedisConnection(HOST)
    
    def __init__(self, ip, rfsoc_name) -> None:
        """Bread and butter of the RFSOC object. This is the main object that facilitates control over the readout system.

        :param ip: _description_
        :type ip: _type_
        :param rfsoc_number: _description_
        :type rfsoc_number: _type_
        """
        log.debug(f"rfsoc object created {rfsoc_name} {ip}")
        self.name = rfsoc_name
        self._ch1 = rfchannel()
        self._ch2 = rfchannel()


    def upload_bitstream(self, path: str):
        """Command the RFSoC to upload(or reupload) it's FPGA Firmware"""
        assert isinstance(path, str) == True, "Path should be a string"
        args = {
                "abs_bitstream_path" : path
                }

   
    def config_hardware(self, srcip, dstip, dstmac):
        """The RFSoC has several hardware configurations that need to be set before it can be used. This function sets those configurations.

        :param srcip: IP address the RFSoC will use to send data
        :type srcip: str
        :param dstip: IP address the host computer will use to receive data from the RFSoC.
        :type dstip: str
        :param srcmac: MAC address of the RFSoC
        :type srcmac: str
        :param dstmac: MAC address of the host computer network interface
        :type dstmac: str
        """
        if len(dstmac) != 12:
            log.warning("bad mac address, expected 12 characters")
            return
        data = {}
        data['data_a_srcip'] = ''
        data['data_b_srcip'] = ''
        data['destmac_msb'] = ''
        data['destmac_lsb'] = ''






    def set_tone_list(self, chan=1, tonelist=[], amplitudes=[]):
        """Set a DAC channel to generate a signal from a list of tones

        :param chan: The DAC channel on the RFSoC to set, defaults to 1
        :type chan: int, optional
        :param tonelist: list of tones in MHz to generate, defaults to []
        :type tonelist: list, optional    def upload_bitstream(self):
        """Command the RFSoC to upload(or reupload) it's FPGA Firmware"""
        pass
        :param amplitudes: list of tone powers per tone, Normalized to 1, defaults to []
        :type amplitudes: list, optional
        """
        uuid = uuid4()
        if chan == 1:
            self._ch1.baseband_freqs = tonelist
            self._ch1.tone_powers = amplitudes
            self._ch1.n_tones = len(tonelist)

        elif chan == 2:
            self._ch2.baseband_freqs = tonelist
            self._ch2.tone_powers = amplitudes
        else:
            log.error(f"Invalid channel number {chan}")

        pass

    def set_alist(self, chan, alist):
        pass

    def get_tone_list(self, chan=None):
        pass

    def get_last_alist(self, chan):
        pass


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
        self.n_tones = 0    def upload_bitstream(self):
        """Command the RFSoC to upload(or reupload) it's FPGA Firmware"""
        pass

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


class RedisConnection:
    def __init__(self) -> None:
        self.r = redis.Redis(host=HOST, port=6379)

        if self.is_connected():
            self.pubsub = self.r.pubsub()
            self.pubsub.subscribe("REPLY")
            log.debug(self.pubsub.get_message())

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

    def issue_command(self, rfsocname, command, timeout):
        """Issues a command via redis to the RFSoC and waits for a response or timeout.
        Returns an error if a timeout occurs.

        :param command: _description_
        :type command: _type_
        :param timeout: _description_
        :type timeout: _type_
        """
       
        if not self.is_connected():
            log.error("NOT CONNECTED TO REDIS SERVER")
            return

        uuid = str(uuid.uuid4())
        cmddict = {
            "command" : command,
            "uuid" : uuid, 
            "data" : args,
            }  

        log.debug(f"Issuing command payload {cmddict} with timeout {timeout}; uuid: {uuid}")
        self.r.publish("rfsoc", cmddict) 
        response = self.pubsub.get_message(timeout=timeout) 
        if response is None:
            log.warning("received no response from RFSOC within specified timeout period")
            return None
        # see command reference format in docs
        try:
            if response['type'] == "message":
                body = response['data']
                body = json.loads(body.decode())
                status = body['status']
                error = body['error']
                reply_uuid = body['uuid']
                data = body['data']
                if reply_uuid != uuid:
                    log.warning(f"reply UUID did not match message uuid as expected\nreplyuuid={reply_uuid}, uuid={uuid}")
                    return None
                if status == "OK":
                    log.info("Command Success")
                    return data
                else:
                    log.error(f"rfsoc {rfsocname} reported an error:\n{error}")
                    return None
            else:
                log.error(f"incorrect message type received\n{response}")
                
        except KeyError:
            err = "missing data from reply message"
            log.error(err)
            return

        except json.JSONDecodeError:
            err = "json failed to decode the body of the reply message"
            log.error(err)
            return
        


