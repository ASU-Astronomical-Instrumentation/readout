"""

"""
from scipy import signal, ndimage, fftpack
import matplotlib.pyplot as plt
import numpy as np

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
    if np.mod(len(y),2):
        y = y[0:-1]
    # add the weird padd
    # so, make a backwards copy of the data, then the data, then another backwards copy of the data
    if padd_data:
        y = np.append( np.append(np.flipud(y),y) , np.flipud(y) )
    # take the FFT
    ffty = fftpack.fft(y)
    ffty = fftpack.fftshift(ffty)
    # make the companion frequency array
    delta = 1.0/(len(y)*tau)
    nyquist = 1.0/(2.0*tau)
    freq = np.arange(-nyquist,nyquist,delta)
    # turn this into a positive frequency array
    pos_freq = freq[int(len(ffty)/2):]
    # make the transfer function for the first half of the data
    i_f_3db = min( np.where(pos_freq >= f_3db)[0] )
    f_min = f_3db - (width/2.0)
    i_f_min = min( np.where(pos_freq >= f_min)[0] )
    f_max = f_3db + (width/2);
    i_f_max = min( np.where(pos_freq >= f_max)[0] )
    transfer_function = np.zeros(int(len(y)/2))
    transfer_function[0:i_f_min] = 1
    transfer_function[i_f_min:i_f_max] = (1 + np.sin(-np.pi * ((freq[i_f_min:i_f_max] - freq[i_f_3db])/width)))/2.0
    transfer_function[i_f_max:int(len(freq)/2)] = 0
    # symmetrize this to be [0 0 0 ... .8 .9 1 1 1 1 1 1 1 1 .9 .8 ... 0 0 0] to match the FFT
    transfer_function = np.append(np.flipud(transfer_function),transfer_function)
    # apply the filter, undo the fft shift, and invert the fft
    filtered=np.real(fftpack.ifft(fftpack.ifftshift(ffty*transfer_function)))
    # remove the padd, if we applied it
    if padd_data:
        filtered = filtered[int(len(y)/3):int(2*(len(y)/3))]
    # return the filtered data
    return filtered

# TODO: save data as hdf5
def find_resonators(losweep_file: str, output_file: str, center_freq: float, lo_step: float, smoothing_scale: float,
                    peak_threshold: float, spacing_threshold: float, plot: bool = True):
    """Open target sweep data stored at losweep_file and identify resonant frequencies. The results
    are saved as 2 numpy files indicating the baseband and rf tones.

    :param losweep_file: path to sweep data file
    :type losweep_file: str
    :param output_file: path to output file. This will have _baseband.npy and _rf.npy appended
    :type output_file: str
    :param center_freq: center frequency of target sweep
    :type center_freq: float
    :param lo_step: step size of target sweep
    :type lo_step: float
    :param smoothing_scale: Low pass filter cutoff freq, Hz
    :type smoothing_scale: float
    :param peak_threshold: Amplitude cutoff threshold, dB (e.g., search points <= -6 dB)
    :type peak_threshold: float
    :param spacing_threshold: Frequency spacing threshold, kHz
        if two resonances spaced by <= this amount, choose the deeper one
    :type spacing_threshold: float

    """
    lofreqs, sweepz = np.load(losweep_file)
    # Remove the strange, first 8 tones (8*1000)
    I = sweepz.real.flatten()[8000:]
    Q = sweepz.imag.flatten()[8000:]
    chan_freqs = lofreqs.flatten()[8000:]
    mag = np.sqrt(I ** 2 + Q ** 2)
    mags = 20 * np.log10(mag / np.max(mag))

    newmags = mags
    newfreqs = chan_freqs
    filtermags = lowpass_cosine(newmags, lo_step, 1. / smoothing_scale, 0.1 * (1.0 / smoothing_scale))
    ilo = np.where((newmags - filtermags) < -1.0 * peak_threshold)[0]
    iup = np.where((newmags - filtermags) > -1.0 * peak_threshold)[0]
    new_mags = newmags - filtermags
    new_mags[iup] = 0
    labeled_image, num_objects = ndimage.label(new_mags)
    indices = ndimage.minimum_position(new_mags, labeled_image, np.arange(num_objects) + 1)
    kid_idx = np.array(indices, dtype='int')
    del_idx = []
    for i in range(len(kid_idx) - 1):
        spacing = (newfreqs[kid_idx[i + 1]] - newfreqs[kid_idx[i]])
        if (spacing < spacing_threshold):
            if (new_mags[kid_idx[i + 1]] < new_mags[kid_idx[i]]):
                del_idx.append(i)
            else:
                del_idx.append(i + 1)

    del_idx = np.array(del_idx).astype("int")
    kid_idx = np.delete(kid_idx, del_idx)

    del_again = []
    for i in range(len(kid_idx) - 1):
        spacing = (chan_freqs[kid_idx[i + 1]] - chan_freqs[kid_idx[i]])
        if (spacing < spacing_threshold):
            if (new_mags[kid_idx[i + 1]] < new_mags[kid_idx[i]]):
                del_again.append(i)
            else:
                del_again.append(i + 1)

    del_again = np.array(del_again).astype("int")
    kid_idx = np.delete(kid_idx, del_again)
    # list of kid frequencies
    rf_target_freqs = np.array(chan_freqs[kid_idx]).real
    bb_target_freqs = ((rf_target_freqs) - (center_freq * 1e6))

    if len(bb_target_freqs) > 0:
        bb_target_freqs = np.roll(bb_target_freqs, - np.argmin(np.abs(bb_target_freqs)) - 1)
        np.save(f'{output_file}_baseband.npy', bb_target_freqs.real)
        np.save(f'{output_file}_rf.npy', rf_target_freqs)
        print(len(rf_target_freqs), "KIDs found:\n")
        print(rf_target_freqs.real)
    else:
        print("No freqs found...")

    if plot:
        plt.figure()
        plt.plot(newfreqs, newmags, 'b', label='no filter', alpha=0.3)
        plt.plot(newfreqs, filtermags, 'g', label='filtered', alpha=1)
        plt.xlabel('frequency (Hz)')
        plt.ylabel('dB')
        plt.legend()
        plt.figure()
        plt.plot(newfreqs, newmags - filtermags, 'b', alpha=0.3)
        plt.plot(newfreqs[ilo], newmags[ilo] - filtermags[ilo], 'r.')
        plt.figure()
        plt.plot(newfreqs, newmags, 'b')
        plt.plot(newfreqs[kid_idx], newmags[kid_idx], 'r.')
        plt.xlabel('frequency (Hz)')
        plt.ylabel('dB')
    return