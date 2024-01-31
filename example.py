"""
Description
-----------

This file serves mainly as a scratchpad to determine how the kidpy library will look and feel.

"""
import kidpy3 as kp3


def main():
    r1 = kp3.rfsoc("192.168.2.98", rfsoc_number=1)
    r2 = kp3.rfsoc("192.168.3.98", rfsoc_number=2)
    r1.upload_bitstream()
    r1.config_firmware()
    r1.upload_waveform(chan=1, tonelist=[], amplitudes=[])

    print(r1.connected)
    print(r2.connected)

    r1.ch1.tile_number = 0
    r1.ch2.tile_number = 1
    r2.ch1.tile_number = 2
    r2.ch2.tile_number = 3

    r1.ch1.set_tone_list(...)
    r1.ch2.set_tone_list(...)
    r2.ch1.set_tone_list(...)
    r2.ch2.set_tone_list(...)

    print(
        r1.ch1.get_last_alist(),
        r1.ch2.get_last_alist(),
        r2.ch1.get_last_alist(),
        r2.ch2.get_last_alist()
    )
    if1lo = kp3.valon("/dev/IFSlice1LO")
    if2lo = kp3.valon("/dev/IFSlice2LO")
    atten1 = kp3.onr_ifslice("/dev/IFSlice1Atten")
    atten2 = kp3.onr_ifslice("/dev/IFSlice2Atten")

