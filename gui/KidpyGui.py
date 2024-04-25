import tkinter as tk
from tkinter import ttk
import os


class kidpy3_GUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("KIDPY GUI")
        self.geometry("800x600")  # Set the initial size of the window

        # Create a notebook (Hold all of the different tabs)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both")

        # Create tabs
        config = ttk.Frame(self.notebook)
        waveform_tab = ttk.Frame(self.notebook)
        section3_tab = ttk.Frame(self.notebook)
        section4_tab = ttk.Frame(self.notebook)
        section5_tab = ttk.Frame(self.notebook)

        # Add tabs to the notebook
        self.notebook.add(config, text="CONFIG")
        self.notebook.add(waveform_tab, text="PLACEHOLDER 2")
        self.notebook.add(section3_tab, text="PLACEHOLDER 3")
        self.notebook.add(section4_tab, text="PLACEHOLDER 4")


if __name__ == "__main__":
    app = kidpy3_GUI()
    app.mainloop()
