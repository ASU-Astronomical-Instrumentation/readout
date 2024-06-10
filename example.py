"""
Description
-----------

This is an example of how to use the kidpy3 package to control the RFSOC. 


"""
import kidpy3 as kp3
import numpy as np


def main():
    """
    
    """
    print("Start test")
    rfsoc1 = kp3.RFSOC("192.168.2.128", rfsoc_name="rfsoc1")
    rfsoc1.upload_bitstream("DualChannel-240605.bit")
    rfsoc1.config_hardware("192.168.3.50", "192.168.3.51", "A0CEC8B0C852")
    rfsoc1.set_tone_list(1, [1e6, 12e6, 13e6, 50e6, 125e6, 200e6], [1, 1, 1, 1, 1, 1])
    freqs_up = -1.0*np.linspace(251.0e6,1.0e6,500)
    freqs_lw = 1.0*np.linspace(2.25e6,252.25e6,500)
    freqs = np.append(freqs_up,freqs_lw)
    rfsoc1.set_tone_list(2, freqs, np.ones(1000))
    rfsoc1.set_tone_list(1, [1e6, 12e6, 13e6, 50e6, 125e6, 200e6], [1,1,1,1,1,1])


    

    
    # print(r2.connected)
    # r2 = kp3.RFSOC("192.168.3.96", rfsoc_number=2)
    # r1.ch1.tile_number = 0
    # r1.ch2.tile_number = 1
    # r2.ch1.tile_number = 2
    # r2.ch2.tile_number = 3

    # r1.ch1.set_tone_list(...)
    # r1.ch2.set_tone_list(...)
    # r2.ch1.set_tone_list(...)
    # r2.ch2.set_tone_list(...)

    # print(
    #     r1.ch1.get_last_alist(),
    #     r1.ch2.get_last_alist(),
    #     r2.ch1.get_last_alist(),
    #     r2.ch2.get_last_alist()
    # )
    # if1lo = kp3.valon("/dev/IFSlice1LO")
    # if2lo = kp3.valon("/dev/IFSlice2LO")
    # atten1 = kp3.onr_ifslice("/dev/IFSlice1Atten")
    # atten2 = kp3.onr_ifslice("/dev/IFSlice2Atten")

if __name__ == "__main__":
    main()