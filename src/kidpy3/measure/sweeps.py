
import numpy as plt
import matplotlib.pyplot as np



def revisedsweep():
    """
    Okay we know that we're going to have a band of at least 512 MHz piped through an N=1024 point FFT leaving us with a 500KHz spacing.
    Naturally, with some granularity we'll want to sweep between each point to fill in that spacing. I assume that granularity is 1 KHz
    necessitating n=500 points to take. What if we want to scan much larger bands? We then have to jump large center frequencies on the LO
    in order to center on  a new 512 MHz band +500KHz since we are sweeping. We then repeat the Microsweep, then Jump again I suppose.
    This would be the case if <sweep stop frequency> - <sweep start frequency> exceeded 512 MHz

    idk might shrink this down to 500 Mhz to make a better set of tones.
    """
    pass

def sweep(loSource: valon5009.Synthesizer, udp, f_center, freqs, N_steps=500, freq_step=0.0):
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
    log = logger.getChild("def-sweep")
    tone_diff = np.diff(freqs)[0] / 1e6  # MHz
    log.info(f"tone diff={tone_diff}")
    if freq_step > 0:
        flo_step = freq_step
    else:
        flo_step = tone_diff / N_steps

    log.info(f"lo step size={flo_step}")
    flo_start = f_center - flo_step * N_steps / 2.0  # 256
    flo_stop = f_center + flo_step * N_steps / 2.0  # 256

    flos = np.arange(flo_start, flo_stop, flo_step) #+1e-6
    # flos = np.round(flos * 1e3)*1e-3
    log.info(f"len flos {flos.shape}")
    udp.bindSocket()
    actual_los = []
    def temp(lofreq):
        # self.set_ValonLO function here
 
        # print(lofreq)
        loSource.set_frequency(valon5009.SYNTH_B, lofreq)
        # Read values and trash initial read, suspecting linear delay is cause..
        Naccums = 100
        I, Q = [], []
        for i in range(20):  # toss 10 packets in the garbage
            udp.parse_packet()

        for i in range(Naccums):
            # d = udp.parse_packet()
            d = udp.parse_packet()
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
        Z = Z[start_ind : start_ind + len(freqs)]

        print(".", end="")

        return Z
    sweep_Z = np.array([temp(lofreq) for lofreq in flos])
    log.info(f"sweepz.shape={sweep_Z.shape}")

    f = np.zeros([np.size(freqs), np.size(flos)])
    log.info(f"shape of f = {f.shape}")
    for itone, ftone in enumerate(freqs):
        f[itone, :] = flos * 1.0e6 + ftone
    #    f = np.array([flos * 1e6 + ftone for ftone in freqs]).flatten()
    sweep_Z_f = sweep_Z.T
    #    sweep_Z_f = sweep_Z.T.flatten()
    udp.release()
    ## SAVE f and sweep_Z_f TO LOCAL FILES
    # SHOULD BE ABLE TO SAVE TARG OR VNA
    # WITH TIMESTAMP

    # set the LO back to the original frequency
    loSource.set_frequency(valon5009.SYNTH_B, f_center)

    return (f, sweep_Z_f)


# def targetSweep(ri, udp, valon,**keywords):
#     """Does a sweep centered on the resonances, saves data in targ_savepath
#        as .npy files
#        inputs:
#            roachInterface object ri
#            roach UDP object udp
#            valon synth object valon
#            bool write: Write test comb before sweeping?
#            float span: Sweep span, Hz
#            Navg = Number of data points to average at each sweep step
# 	   keywords are:
#    	   span --specifies custom span rather than from general config
#            lo_step --specifies custom lo step rather than from general config"""
#     if ('span' in keywords):
# 	span = keywords['span']
#     else:
#         span = np.float(gc[np.where(gc == 'targ_span')[0][0]][1])
#     if ('lo_step' in keywords):
#         lo_step_targ = keywords['lo_step']
#     else:
#         lo_step_targ = lo_step
#     Navg = np.int(gc[np.where(gc == 'Navg')[0][0]][1])
#     vna_savepath = str(np.load("last_vna_dir.npy"))
#     if not os.path.exists(targ_savepath):
#         os.makedirs(targ_savepath)
#     sweep_dir = targ_savepath + '/' + \
#        str(int(time.time())) + '-' + time.strftime('%b-%d-%Y-%H-%M-%S') + '.dir'
#     os.mkdir(sweep_dir)
#     np.save("./last_targ_dir.npy", sweep_dir)
#     print sweep_dir
#     target_freqs = np.load(vna_savepath + '/bb_targ_freqs.npy')
#     #target_freqs = np.load("last_freq_comb.npy")
#     np.save(sweep_dir + '/bb_target_freqs.npy', target_freqs)
#     start = center_freq*1.0e6 - (span/2.)
#     stop = center_freq*1.0e6 + (span/2.) 
#     sweep_freqs = np.arange(start, stop, lo_step_targ)
#     sweep_freqs = np.round(sweep_freqs/lo_step_targ)*lo_step_targ
#     np.save(sweep_dir + '/bb_freqs.npy', target_freqs)
#     np.save(sweep_dir + '/sweep_freqs.npy',sweep_freqs)
#     first = True
#     for freq in sweep_freqs:
#         print 'LO freq =', freq/1.0e6, ' MHz'
#         valon.set_frequency(LO, freq/1.0e6)
#         #time.sleep(0.1)
#         udp.saveSweepData(Navg, sweep_dir, freq, len(target_freqs),skip_packets = 25)
#         #time.sleep(0.1)
#     valon.set_frequency(LO, center_freq)
#     return