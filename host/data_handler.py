"""
@author: Cody Roberson
@date: 08/03/2022
@file: data_handler
@copyright: To Be Determined in the Interest of Collaboration
@description:
    DataHandler takes care of generating our hdf5 ovservation data file as well
    as handling any complex operations.

@Revisions:

@Dev Notes:
    20220803: Next step is to give the last of the other variables section their respective attributes.
    This will be followed up with modifying these fn vars such that they become instance vars

"""
import numpy as np
from time import sleep
import h5py
import multiprocessing as mproc

class DataHandler():
    def __init__(self):
        pass

    def create_hdf5_file(self, filename: str, num_packets: int, num_tones: int) -> object:
        """
        Create the skeleton observation data file. Any changes to the observation data format will begin
        here and need to propogate throughout the rest of the codebase.


        :param filename: full h5py datafile path
        :param num_packets: Number of packets to record.
        :param num_tones: Number of baseband tones
        :return:
        """

        DETECTOR_DATA_LENGTH = 2052  # CONST

        data_file = h5py.File(filename, 'w')
        data_file.create_group("observation_data")

        obs_adc_i_data = data_file.create_dataset("observation_data/adc_i", (DETECTOR_DATA_LENGTH / 2, num_packets),
                                                  dtype=h5py.h5t.NATIVE_UINT32, chunks=True)
        obs_adc_i_data.attrs.create("units", "volts")
        obs_adc_i_data.attrs.create("dimension_names", "bin_number, packet_number")

        obs_adc_q_data = data_file.create_dataset("observation_data/adc_q", (DETECTOR_DATA_LENGTH / 2, num_packets),
                                                  dtype=h5py.h5t.NATIVE_UINT32, chunks=True)
        obs_adc_q_data.attrs.create("units", "volts")
        obs_adc_q_data.attrs.create("dimension_names", "bin_number, packet_number")

        obs_azimuth = data_file.create_dataset("observation_data/azimuth", (1, num_packets),
                                               dtype=h5py.h5t.NATIVE_DOUBLE)
        obs_azimuth.attrs.create("units", "degrees")
        obs_azimuth.attrs.create("dimension_names", "azimuth, packet_number")

        obs_elevation = data_file.create_dataset("observation_data/elevation", (1, num_packets),
                                                 dtype=h5py.h5t.NATIVE_DOUBLE)
        obs_elevation.attrs.create("units", "degrees")
        obs_elevation.attrs.create("dimension_names", "elevation, packet_number")

        obs_lofreq = data_file.create_dataset("observation_data/lofrequency", (1, num_packets),
                                              dtype=h5py.h5t.NATIVE_DOUBLE)
        obs_lofreq.attrs.create("units", "Hz")
        obs_lofreq.attrs.create("dimension_names", "lofrequency, packet_number")

        # Custom Timeframe
        timestamp_compound_datatype = [
            ("year", h5py.h5t.NATIVE_UINT32),
            ("month", h5py.h5t.NATIVE_UINT32),
            ("day", h5py.h5t.NATIVE_UINT32),
            ("seconds_midnight", h5py.h5t.NATIVE_UINT32),
            ("packet_number", h5py.h5t.NATIVE_UINT64),
        ]
        obs_timestamp = data_file.create_dataset("observation_data/timestamp", dtype=timestamp_compound_datatype,
                                                 shape=(num_packets, 1))

        data_file.create_group("other_variables")
        oth_atten = data_file.create_dataset("other_variables/attenuator_settings", dtype=h5py.h5t.NATIVE_DOUBLE,
                                             shape=(4, 1))
        oth_atten.attrs.create("units", "dB")

        oth_bbfreq = data_file.create_dataset("other_variables/baseband_freqs", dtype=h5py.h5t.NATIVE_DOUBLE, shape=(num_tones, 1))
        oth_chanmask = data_file.create_dataset("other_variables/channel_mask", dtype=h5py.h5t.NATIVE_INT32, shape=(num_tones, 1))
        oth_deltax = data_file.create_dataset("other_variables/detector_delta_x", dtype=h5py.h5t.NATIVE_DOUBLE, shape=(num_tones, 1))
        oth_deltay = data_file.create_dataset("other_variables/detector_delta_y", dtype=h5py.h5t.NATIVE_DOUBLE, shape=(num_tones, 1))
        oth_globaz = data_file.create_dataset("other_variables/global_delta_azimuth", dtype=h5py.h5t.NATIVE_DOUBLE)
        oth_globel = data_file.create_dataset("other_variables/global_delta_elevation", dtype=h5py.h5t.NATIVE_DOUBLE)
        oth_samplerate = data_file.create_dataset("other_variables/sample_rate", dtype=h5py.h5t.NATIVE_DOUBLE)
        oth_timenum = data_file.create_dataset("other_variables/tile_number", dtype=h5py.h5t.NATIVE_UINT32, shape=(num_tones, 1))
        oth_tonepw = data_file.create_dataset("other_variables/tone_power", dtype=h5py.h5t.NATIVE_DOUBLE, shape=(num_tones, 1))


def DoTestRoutine():
    pass

if __name__ == "__main__":
    DoTestRoutine()