import tkinter as tk
from tkinter import ttk
import os
import config

PADDING = 10

class kidpy3_GUI(tk.Tk):
    def __init__(self):
        super().__init__()

        cfg = config.load_config()
        self.title("KIDPY GUI")
        self.geometry("800x600")  # Set the initial size of the window

        # Create a notebook (Hold all of the different tabs)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both")

        # Create tabs
        maintab = ttk.Frame(self.notebook)
        section2_tab = ttk.Frame(self.notebook)
        section3_tab = ttk.Frame(self.notebook)
        section4_tab = ttk.Frame(self.notebook)

        # Add tabs to the notebook
        self.notebook.add(maintab, text="MAIN TAB")
        self.notebook.add(section2_tab, text="PLACEHOLDER 2")
        self.notebook.add(section3_tab, text="PLACEHOLDER 3")
        self.notebook.add(section4_tab, text="PLACEHOLDER 4")

        firmware_frame = tk.LabelFrame(maintab, text="Firmware")
        waveform_frame = tk.LabelFrame(maintab, text="Waveform")

        # Create labels
        label1 = ttk.Label(firmware_frame, text="Source IP for RFSOC <1> Data Channel 1:")
        label2 = ttk.Label(firmware_frame, text="Source IP for RFSOC <1> Data Channel 2:")
        label3 = ttk.Label(firmware_frame, text="RFSOC <1> Destination MAC Address:")
        label4 = ttk.Label(firmware_frame, text="Source IP for RFSOC <2> Data Channel 1:")
        label5 = ttk.Label(firmware_frame, text="Source IP for RFSOC <2> Data Channel 2:")
        label6 = ttk.Label(firmware_frame, text="RFSOC <2> Destination MAC Address:")

        # Create text boxes
        textbox1 = ttk.Entry(firmware_frame)
        textbox2 = ttk.Entry(firmware_frame)
        textbox3 = ttk.Entry(firmware_frame)
        textbox1.insert(0, cfg["DEFAULT"]["rf1dchan1"])
        textbox2.insert(0, cfg["DEFAULT"]["rf1dchan2"])
        textbox3.insert(0, cfg["DEFAULT"]["rf1dstmac"])

        textbox4 = ttk.Entry(firmware_frame, )
        textbox5 = ttk.Entry(firmware_frame)
        textbox6 = ttk.Entry(firmware_frame)
        textbox4.insert(0, cfg["DEFAULT"]["rf2dchan1"])
        textbox5.insert(0, cfg["DEFAULT"]["rf2dchan2"])
        textbox6.insert(0, cfg["DEFAULT"]["rf2dstmac"])

        # Create button
        btn_setreg = ttk.Button(firmware_frame, text="Set Registers")
        btn_ulbit = ttk.Button(firmware_frame, text="Upload Bitstream")
        firmware_frame.pack()
        waveform_frame.pack()

        # Add labels, text boxes, and button to maintab
        label1.grid(row=0, column=0, padx=PADDING, pady=PADDING)
        label2.grid(row=1, column=0, padx=PADDING, pady=PADDING)
        label3.grid(row=2, column=0, padx=PADDING, pady=PADDING)
        label4.grid(row=3, column=0, padx=PADDING, pady=PADDING)
        label5.grid(row=4, column=0, padx=PADDING, pady=PADDING)
        label6.grid(row=5, column=0, padx=PADDING, pady=PADDING)
        textbox1.grid(row=0, column=1, padx=PADDING, pady=PADDING)
        textbox2.grid(row=1, column=1, padx=PADDING, pady=PADDING)
        textbox3.grid(row=2, column=1, padx=PADDING, pady=PADDING)
        textbox4.grid(row=3, column=1, padx=PADDING, pady=PADDING)
        textbox5.grid(row=4, column=1, padx=PADDING, pady=PADDING)
        textbox6.grid(row=5, column=1, padx=PADDING, pady=PADDING)
        btn_setreg.grid(row=6, column=1, columnspan=1, padx=PADDING, pady=PADDING)
        btn_ulbit.grid(row=6, column=0, columnspan=1, padx=PADDING, pady=PADDING)




        label7 = ttk.Label(waveform_frame, text="Custom Frequency Comb:")
        label8 = ttk.Label(waveform_frame, text="Pre-baked Waveforms")
        button_setwv = ttk.Button(waveform_frame, text="Set Waveform")
        button_setwv.grid(row=2, column=1, columnspan=2, padx=PADDING, pady=PADDING)
        textbox4 = ttk.Entry(waveform_frame, width=50)
        textbox4.grid(row=0, column=1, padx=PADDING, pady=PADDING, columnspan=4)
        label7.grid(row=0, column=0, padx=PADDING, pady=PADDING)
        label8.grid(row=1, column=0, padx=PADDING, pady=PADDING)
        radio1var = tk.IntVar(0)
        ttk.Radiobutton(waveform_frame, text="Custom", value=0, variable=radio1var).grid(row=1, column=1, padx=PADDING, pady=PADDING)
        ttk.Radiobutton(waveform_frame, text="10 Tones", value=1, variable=radio1var).grid(row=1, column=2, padx=PADDING, pady=PADDING)
        ttk.Radiobutton(waveform_frame, text="100 Tones", value=2, variable=radio1var).grid(row=1, column=3, padx=PADDING, pady=PADDING)
        ttk.Radiobutton(waveform_frame, text="1000 Tones", value=3, variable=radio1var).grid(row=1, column=4, padx=PADDING, pady=PADDING)

if __name__ == "__main__":
    app = kidpy3_GUI()
    app.mainloop()
