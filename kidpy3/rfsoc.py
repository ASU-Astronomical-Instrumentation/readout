import numpy as np

class rfsoc:
    def __init__(self) -> None:
        self.connected = False
        self.ch1 = rfchannel()
        self.ch2 = rfchannel()
        pass

    def config_firmware(self):

        pass
    
    def upload_bitstream(self):
        pass

    def upload_waveform(chan=1, tonelist=[], amplitudes=[]):
        pass

class rfchannel:
    def __init__(self, raw_filename) -> None:
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

        self.raw_filename = raw_filename
        self.ip = ""  #udop datastream IP address.
        self.baseband_freqs = np.empty(2) #empty ndarray
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
    
    def set_tone_list():
        pass

    def set_alist():
        pass

    def get_tone_list():
        pass

    def get_last_alist():
        pass