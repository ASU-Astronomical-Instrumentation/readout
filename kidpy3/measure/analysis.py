"""

"""

from __future__ import annotations
from typing import Callable, Iterable
from pathlib import Path
import h5py
from scipy import signal, ndimage, fftpack
import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
import os


def lowpass_cosine(y, tau, f_3db, width, padd_data=True):
    """Applies a raised cosine low-pass filter to the sweep data
    ***Code/inner comments provided by Sean Bryan***
    inputs:
        float y: array of input data to operate on
        float tau: frequency step size of sweep,
        f_3db: 1/smoothing scale (3 dB cutoff) specified in general config
        width: Scaling factor for f_3dB
        bool padd_data: See inner comment below
    outputs:
        filtered: filtered sweep data"""
    # padd_data = True means we are going to symmetric copies of the data to the start and stop
    # to reduce/eliminate the discontinuities at the start and stop of a dataset due to filtering
    # False means we're going to have transients at the start and stop of the data
    # kill the last data point if y has an odd length
    if np.mod(len(y), 2):
        y = y[0:-1]
    # add the weird padd
    # so, make a backwards copy of the data, then the data, then another backwards copy of the data
    if padd_data:
        y = np.append(np.append(np.flipud(y), y), np.flipud(y))
    # take the FFT
    ffty = fftpack.fft(y)
    ffty = fftpack.fftshift(ffty)
    # make the companion frequency array
    delta = 1.0 / (len(y) * tau)
    nyquist = 1.0 / (2.0 * tau)
    freq = np.arange(-nyquist, nyquist, delta)
    # turn this into a positive frequency array
    pos_freq = freq[int(len(ffty) / 2) :]
    # make the transfer function for the first half of the data
    i_f_3db = min(np.where(pos_freq >= f_3db)[0])
    f_min = f_3db - (width / 2.0)
    i_f_min = min(np.where(pos_freq >= f_min)[0])
    f_max = f_3db + (width / 2)
    i_f_max = min(np.where(pos_freq >= f_max)[0])
    transfer_function = np.zeros(int(len(y) / 2))
    transfer_function[0:i_f_min] = 1
    transfer_function[i_f_min:i_f_max] = (
        1 + np.sin(-np.pi * ((freq[i_f_min:i_f_max] - freq[i_f_3db]) / width))
    ) / 2.0
    transfer_function[i_f_max : int(len(freq) / 2)] = 0
    # symmetrize this to be [0 0 0 ... .8 .9 1 1 1 1 1 1 1 1 .9 .8 ... 0 0 0] to match the FFT
    transfer_function = np.append(np.flipud(transfer_function), transfer_function)
    # apply the filter, undo the fft shift, and invert the fft
    filtered = np.real(fftpack.ifft(fftpack.ifftshift(ffty * transfer_function)))
    # remove the padd, if we applied it
    if padd_data:
        filtered = filtered[int(len(y) / 3) : int(2 * (len(y) / 3))]
    # return the filtered data
    return filtered


class ResonatorFinder:
    """
    Facilitates finding resonators when their approximate locations in frequency are not known. This class relies on processing data from
    the lo sweep function or class (depending on implementation)

    The user should init this object. Call find(...) followed by plot(...) until the desired parameters are set. Then follow up with save_h5(...)
    Data can then be saved(appended) to a specified hdf5 file.

    """
    def __init__(
        self,
        sweep_data: (tuple[npt.NDArray, npt.NDArray]) | str | Path,
        center_freq: float,
        lo_step: float,
    ):

        # Grab data from an HDF5 file else grab data directly
        if isinstance(sweep_data, str) or isinstance(sweep_data, Path):
            if not os.path.exists(sweep_data):
                raise FileNotFoundError("Couldn't find sweep data from path specified")
            with h5py.File(sweep_data, "r") as fh:
                try:
                    self.sweep_data = fh["global_data/lo_sweep"][...]
                except KeyError:
                    # Yes, I felt bad writing this.
                    raise KeyError(
                        "Expected to find the lo_sweep dataset within the global_data group but none was found"
                    )
        else:
            self.sweep_data = sweep_data
        self.rf_target_freqs = np.zeros((1,))
        self.bb_target_freqs = np.zeros((1,))
        self.center_freq = center_freq
        self.lo_step = lo_step
        self.smoothing_scale = 0.0
        self.peak_threshold = 0.0
        self.spacing_threshold = 0.0

    def save_h5(self, path: Path | str):
        if not os.path.exists(path):
            raise FileNotFoundError("Couldn't find sweep data from path specified")

        with h5py.File(path, "a") as fh:
            fh.create_dataset(
                "global_data/r_finder/rf_target_freqs", data=self.rf_target_freqs
            )
            fh.create_dataset(
                "global_data/r_finder/bb_target_freqs", data=self.bb_target_freqs
            )
            fh.create_dataset("global_data/r_finder/center_freq", data=self.center_freq)
            fh.create_dataset("global_data/r_finder/lo_step", data=self.lo_step)
            fh.create_dataset(
                "global_data/r_finder/smoothing_scale", data=self.smoothing_scale
            )
            fh.create_dataset(
                "global_data/r_finder/peak_threshold", data=self.peak_threshold
            )
            fh.create_dataset(
                "global_data/r_finder/spacing_threshold", data=self.spacing_threshold
            )

    def save_npy(self, path: Path | str):
        raise NotImplemented

    
    def plot(self):
        (lofreqs, sweepz) = self.sweep_data
        I = sweepz.real.flatten()[8000:]
        Q = sweepz.imag.flatten()[8000:]
        lofreqs = lofreqs.flatten()[8000:]
        filtermags = self._filtermags
        ilo = self._ilo

        kid_idx = self._kididx
        mag = np.sqrt(I**2 + Q**2)
        mags = 20 * np.log10(mag / np.max(mag))

        plt.figure()
        plt.plot(lofreqs, mags, "b", label="no filter", alpha=0.3)
        plt.plot(lofreqs, filtermags, "g", label="filtered", alpha=1)
        plt.xlabel("frequency (Hz)")
        plt.ylabel("dB")
        plt.legend()
        plt.figure()
        plt.plot(lofreqs, mags - filtermags, "b", alpha=0.3)
        plt.plot(lofreqs[ilo], mags[ilo] - filtermags[ilo], "r.")
        plt.figure()
        plt.plot(lofreqs, mags, "b")
        plt.plot(lofreqs[kid_idx], mags[kid_idx], "r.")
        plt.xlabel("frequency (Hz)")
        plt.ylabel("dB")

    def find_resonators(self,
        smoothing_scale: float,
        peak_threshold: float,
        spacing_threshold: float,
    ):
        """
        Parameters:
            lo_sweep_data (tuple[npt.NDArray, npt.NDArray]): Lo Sweep Data.
                This function expects a tuple containing probetones and resultant s21
            center_freq (float): center frequency with which the sweep was performed
            lo_step (float): Step size of the LO sweep
            smoothing_scale (float): Low pass filter cutoff freq, Hz
            peak_threshold (float): Amplitude cutoff threshold, dB (e.g., search points <= -6 dB)
            spacing_threshold (float): Frequency spacing threshold, kHz
                if two resonances spaced by <= this amount, choose the deeper one
        """

        (lofreqs, sweepz) = self.sweep_data
        # Remove the strange, first 8 tones (8*1000)
        I = sweepz.real.flatten()[8000:]
        Q = sweepz.imag.flatten()[8000:]
        chan_freqs = lofreqs.flatten()[8000:]
        mag = np.sqrt(I**2 + Q**2)
        mags = 20 * np.log10(mag / np.max(mag))

        self.mags = mags
        newmags = mags
        newfreqs = chan_freqs
        filtermags = lowpass_cosine(
            newmags, lo_step, 1.0 / smoothing_scale, 0.1 * (1.0 / smoothing_scale)
        )
        ilo = np.where((newmags - filtermags) < -1.0 * peak_threshold)[0]
        self.ilo = ilo
        iup = np.where((newmags - filtermags) > -1.0 * peak_threshold)[0]
        self.iup = iup
        new_mags = newmags - filtermags
        new_mags[iup] = 0
        labeled_image, num_objects = ndimage.label(new_mags)
        indices = ndimage.minimum_position(
            new_mags, labeled_image, np.arange(num_objects) + 1
        )
        kid_idx = np.array(indices, dtype="int")
        del_idx = []
        for i in range(len(kid_idx) - 1):
            spacing = newfreqs[kid_idx[i + 1]] - newfreqs[kid_idx[i]]
            if spacing < spacing_threshold:
                if new_mags[kid_idx[i + 1]] < new_mags[kid_idx[i]]:
                    del_idx.append(i)
                else:
                    del_idx.append(i + 1)

        del_idx = np.array(del_idx).astype("int")
        kid_idx = np.delete(kid_idx, del_idx)

        del_again = []
        for i in range(len(kid_idx) - 1):
            spacing = chan_freqs[kid_idx[i + 1]] - chan_freqs[kid_idx[i]]
            if spacing < spacing_threshold:
                if new_mags[kid_idx[i + 1]] < new_mags[kid_idx[i]]:
                    del_again.append(i)
                else:
                    del_again.append(i + 1)

        del_again = np.array(del_again).astype("int")
        kid_idx = np.delete(kid_idx, del_again)
        # list of kid frequencies
        rf_target_freqs = np.array(chan_freqs[kid_idx]).real
        bb_target_freqs = (rf_target_freqs) - (center_freq * 1e6)

        bbTargFleng = len(bb_target_freqs)
        if bbTargFleng > 0:
            bb_target_freqs = np.roll(
                bb_target_freqs, -np.argmin(np.abs(bb_target_freqs)) - 1
            )
        return bbTargFleng
