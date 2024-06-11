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
    4 : "set_tone_list on Chan2:rfsoc1"
    }



def main():
    """
    
    """
    rfsoc1 = kp3.RFSOC("192.168.2.128", rfsoc_name="rfsoc2")
    try:
        while True:
            for opt in CONTROLS:
                print(f"{opt} : {CONTROLS[opt]}")
            
            choice = int(input("Enter the option number: "))
        
            if choice == 1:
                rfsoc1.upload_bitstream("DualChannel-240605.bit")
            elif choice == 2:
                rfsoc1.config_hardware("192.168.3.50", "192.168.3.51", "A\io0CEC8B0C852")
            elif choice == 3:
                rfsoc1.set_tone_list(1, [1e6, 12e6, 13e6, 50e6, 125e6, 200e6], [1, 1, 1, 1, 1, 1])
            elif choice == 4:
                freqs_up = -1.0*np.linspace(251.0e6,1.0e6,500)
                freqs_lw = 1.0*np.linspace(2.25e6,252.25e6,500)
                freqs = np.append(freqs_up,freqs_lw)
                rfsoc1.set_tone_list(2, freqs, np.ones(1000))
            else:
                print("Invalid choice")
            os.system("sleep 3; clear")
    except KeyboardInterrupt:
        print("Exiting the program")
        exit(0)


if __name__ == "__main__":
    main()