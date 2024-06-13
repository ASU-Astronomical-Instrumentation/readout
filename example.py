"""
Description
-----------

This is an example of how to use the kidpy3 package to control the RFSOC. 


"""
import kidpy3 as kp3
import numpy as np
import os


CONTROLS = {
    1 : "Upload bitstream to rfsoc1",
    2 : "Configure hardware on rfsoc1",
    3 : "Set tone list on Chan1:rfsoc1",
    4 : "set_tone_list on Chan2:rfsoc1",
    5 : "Upload bitstream to rfsoc2",
    6 : "Configure hardware on rfsoc2",
    7 : "Set tone list on Chan1:rfsoc2",
    8 : "set_tone_list on Chan2:rfsoc2",
    9 : "Upload bitstream to rfsoc3",
    10 : "Configure hardware on rfsoc3",
    11 : "Set tone list on Chan1:rfsoc3",
    12 : "set_tone_list on Chan2:rfsoc3",
    }



def main():
    """
    
    """
    rfsoc1 = kp3.RFSOC("192.168.2.10", rfsoc_name="rfsoc1")
    rfsoc2 = kp3.RFSOC("192.168.2.10", rfsoc_name="rfsoc2")
    rfsoc3 = kp3.RFSOC("192.168.2.10", rfsoc_name="rfsoc3")
    try:
        while True:
            for opt in CONTROLS:
                print(f"{opt} : {CONTROLS[opt]}")
            
            choice = int(input("Enter the option number: "))
        
            if choice == 1:
                rfsoc1.upload_bitstream("DualChannel-240605.bit")
            elif choice == 2:
                rfsoc1.config_hardware("192.168.3.50", "192.168.3.51", "A0CEC8B0C852")
            elif choice == 3:
                rfsoc1.set_tone_list(1, [1e6, 12e6, 13e6, 50e6, 125e6, 200e6], [1, 1, 1, 1, 1, 1])
            elif choice == 4:
                freqs_up = -1.0*np.linspace(251.0e6,1.0e6,500)
                freqs_lw = 1.0*np.linspace(2.25e6,252.25e6,500)
                freqs = np.append(freqs_up,freqs_lw)
                rfsoc1.set_tone_list(2, freqs, np.ones(1000))
            elif choice == 5:
                rfsoc2.upload_bitstream("DualChannel-240605.bit")
            elif choice == 6:
                rfsoc2.config_hardware("192.168.3.52", "192.168.3.53", "A0CEC8B0C852")
            elif choice == 7:
                rfsoc2.set_tone_list(1, [106.6e6, 111.115e6], [1, 1])
            elif choice == 8:
                freqs_up = -1.0*np.linspace(251.0e6,1.0e6,500)
                freqs_lw = 1.0*np.linspace(2.25e6,252.25e6,500)
                freqs = np.append(freqs_up,freqs_lw)
                rfsoc2.set_tone_list(2, freqs, np.ones(1000))
            elif choice == 9:
                rfsoc3.upload_bitstream("DualChannel-240605.bit")
            elif choice == 10:
                rfsoc3.config_hardware("192.168.3.54", "192.168.3.55", "A0CEC8B0C852")
            elif choice == 11:
                rfsoc3.set_tone_list(1, [106.6e6, 111.115e6], [1, 1])
            elif choice == 12:
                freqs_up = -1.0*np.linspace(251.0e6,1.0e6,500)
                freqs_lw = 1.0*np.linspace(2.25e6,252.25e6,500)
                freqs = np.append(freqs_up,freqs_lw)
                rfsoc3.set_tone_list(2, freqs, np.ones(1000))
            else:
                print("Invalid choice")
            
            os.system("sleep 3; clear")
    except KeyboardInterrupt:
        print("Exiting the program")
        exit(0)


if __name__ == "__main__":
    main()
