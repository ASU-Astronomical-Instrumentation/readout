"""
Description
-----------

This is an example of how to use the kidpy3 package to control the RFSOC. 


"""
import kidpy3 as kp3
import numpy as np
import extra_hardware.valon5009.valon as valon
# import matplotlib.pyplot as plt
import extra_hardware.transceiver320_d.transceiver as ts
from kidpy3.udp2 import udpcap


CONTROLS = {
    1 : "<DISABLED> Upload bitstream to rfsoc1",
    2 : "<>Configure hardware on rfsoc1",
    3 : "Set Chan1 rfsoc1 to a full comb",
    4 : "LO Sweep",
    5 : "set lo to 1000 MHz",
    6 : "set attenuation",
    7 : "set chan1 to 100 tones",
    8 : "set chan1 to 10 tones"
}


def oldmain():
    """

    """
    r1 = kp3.RFSOC("./rfsoc_config_default.yml")
    freqs_up = -1.0 * np.linspace(241.0e6, 1.0e6, 430)
    freqs_lw = 1.0 * np.linspace(2.25e6, 242.25e6, 453)
    freqs = np.append(freqs_up, freqs_lw)

    fset2 =   np.append(-1.0 * np.linspace(251.0e6, 1.0e6, 50),
                        1.0 * np.linspace(2.8e6, 252.25e6, 50))

    fset3 =   np.append(-1.0 * np.linspace(251.0e6, 1.0e6, 5),
                        1.0 * np.linspace(2.25e6, 252.25e6, 5))

    attens = ts.Transceiver("/dev/ttyACM0")


    lo_source = valon.Synthesizer("/dev/exclaim_lo")
    lo_source.set_rf_level(2, 15.0)
    lo_source.set_rf_level(1, 15.0)
    port = udpcap()
    try:
        while True:
            for opt in CONTROLS:
                print(f"{opt} : {CONTROLS[opt]}")

            choice = int(input("Enter the option number: "))
            if choice == 3:
                r1.set_tone_list(1, freqs, np.ones_like(freqs))
            elif choice == 4:
                kp3.science.loSweep(lo_source, port, freqs, 1000, N_steps=500,
                                    savefile="/data/noise_20240913/")
            elif choice == 5:
                lo_source.set_frequency(2, 1000)
                lo_source.set_frequency(1, 1000)
            elif choice == 6:
                try:
                    a = int(input("Attenuator Address?  "))
                    b = float(input("Attenuation?  "))
                    attens.set_atten(a,b)
                except ValueError:
                    print("try harder next time")
                except KeyboardInterrupt:
                    break
            elif choice == 7:
                r1.set_tone_list(1, fset2, np.ones_like(fset2))
            elif choice == 8:
                r1.set_tone_list(1, fset3, np.ones_like(fset3))

            else:
                print("Invalid choice")
            # os.system("sleep 3; clear")
    except KeyboardInterrupt:
        print("\nExiting the program")
        exit(0)



if __name__ == "__main__":
    oldmain()
