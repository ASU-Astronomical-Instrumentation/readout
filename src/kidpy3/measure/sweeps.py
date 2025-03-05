import numpy as np
import matplotlib.pyplot as plt
import h5py
from ..data_handler import Rfchan
from ..udp2 import capture_packets
from ..hardware import Valon5009

SYNTH_A = 1
SYNTH_B = 2

def losweep(loSource: Valon5009, channel: Rfchan, f_center, freqs, N_steps=500, freq_step=0.0, naccums=100):
    """
    Actually perform an LO Sweep using valon 5009's and save the data

    :param loSource:
        Valon 5009 Device Object instance
    :type loSource: valon5009.Synthesizer
    :param f_center:
        Center frequency of upconverted tones
    :param freqs: List of Baseband Frequencies returned from rfsocInterface.py's writeWaveform()
    :type freqs: List

    :param udp: udp data capture utility. This is our bread and butter for taking data from ethernet
    :type udp: udpcap.udpcap object instance

    :param N_steps: Number of steps with which to do the sweep.
    :type N_steps: Int

    Credit: Dr. Adrian Sinclair (adriankaisinclair@gmail.com)
    """
    tone_diff = np.diff(freqs)[0] / 1e6  # MHz

    if freq_step > 0:
        flo_step = freq_step
    else:
        flo_step = tone_diff / N_steps

    flo_start = f_center - flo_step * N_steps / 2.0  # 256
    flo_stop = f_center + flo_step * N_steps / 2.0  # 256

    flos = np.arange(flo_start, flo_stop, flo_step)  # +1e-6


    actual_los = []

    def temp(lofreq):

        loSource.set_frequency(SYNTH_B, lofreq)
        I, Q = [], []

        # Read values and trash initial read, suspecting linear delay is cause.
        capture_packets(channel, 20)

        for i in range(naccums):
            # d = udp.parse_packet()
            d = capture_packets(channel, 1)[:, 0]
            It = d[::2]
            Qt = d[1::2]
            I.append(It)
            Q.append(Qt)
        I = np.array(I)
        Q = np.array(Q)
        Imed = np.median(I, axis=0)
        Qmed = np.median(Q, axis=0)

        Z = Imed + 1j * Qmed
        start_ind = np.min(np.argwhere(Imed != 0.0))
        Z = Z[start_ind: start_ind + len(freqs)]

        print(".", end="")

        return Z

    sweep_Z = np.array([temp(lofreq) for lofreq in flos])

    f = np.zeros([np.size(freqs), np.size(flos)])

    for itone, ftone in enumerate(freqs):
        f[itone, :] = flos * 1.0e6 + ftone
    #    f = np.array([flos * 1e6 + ftone for ftone in freqs]).flatten()
    sweep_Z_f = sweep_Z.T
    #    sweep_Z_f = sweep_Z.T.flatten()
    ## SAVE f and sweep_Z_f TO LOCAL FILES
    # SHOULD BE ABLE TO SAVE TARG OR VNA
    # WITH TIMESTAMP

    # set the LO back to the original frequency
    loSource.set_frequency(SYNTH_B, f_center)

    return (f, sweep_Z_f)


def target_sweep(losource, channel, f_center ):
    """
    Is there actually a difference between this and lo sweep
    """
    pass












