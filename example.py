"""
Description
-----------

This is an example of how to use the kidpy3 package to control the RFSOC. 


"""
import kidpy3 as kp3



def main():
    """
    
    """
    r1 = kp3.RFSOC("192.168.2.98", rfsoc_name="rfsoc1")
    r2 = kp3.RFSOC("192.168.2.98", rfsoc_name="rfsoc2")
    r1.upload_bitstream()
    r1.config_hardware("asdf", "asdf", "asdf", "asdf")
    kp3.libcapture([r1, r2])


    
    
    
    
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