import tkinter as tk
from tkinter import ttk
import os

class kidpy3_GUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("KIDPY GUI MOCKUP")
        self.geometry("800x600")  # Set the initial size of the window

        # Create a notebook (Hold all of the different tabs)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both")

        # Create tabs
        settings_tab = ttk.Frame(self.notebook)
        waveform_tab = ttk.Frame(self.notebook)
        section3_tab = ttk.Frame(self.notebook)
        section4_tab = ttk.Frame(self.notebook)
        section5_tab = ttk.Frame(self.notebook)
        
        # Add tabs to the notebook
        self.notebook.add(settings_tab, text="PLACEHOLDER 1")
        self.notebook.add(waveform_tab, text="PLACEHOLDER 2")
        self.notebook.add(section3_tab, text="PLACEHOLDER 3")
        self.notebook.add(section4_tab, text="PLACEHOLDER 4")

        # # Add widgets to the "Settings" tab
        tk.Label(settings_tab, text="Redis IP Address:").grid(row=1, column=0, sticky=tk.E)
        tk.Entry(settings_tab).grid(row=1, column=1, padx=5, pady=5)

        # # ... (other widgets for the "Settings" tab)

        tk.Label(settings_tab, text="Select File:").grid(row=5, column=0, sticky=tk.E)
        self.file_combo = ttk.Combobox(settings_tab, state="readonly", values=self.get_files_from_folder())
        self.file_combo.grid(row=5, column=1, pady=5)

        # Add widgets to the "Section 2" tab
        tk.Label(waveform_tab, text="Select .npy File:").grid(row=1, column=0, sticky=tk.E)
        self.npy_file_combo = ttk.Combobox(waveform_tab, state="readonly", values=self.get_npy_files_from_folder())
        self.npy_file_combo.grid(row=1, column=1, pady=5)

        tk.Label(section3_tab, text="Slice 1, System 1").grid(row=1, column=1, sticky=tk.W)
        tk.Label(section3_tab, text="RFOUT").grid(row=2, column=1, sticky=tk.E)
        tk.Label(section3_tab, text="RFIN").grid(row=3, column=1, sticky=tk.E)
        self.sect3_entry = tk.Entry(section3_tab)
        self.sect3_entry.grid(row=2, column=2, sticky=tk.W)
        self.sect3_entry2 = tk.Entry(section3_tab)
        self.sect3_entry2.grid(row=3, column=2, sticky=tk.W)

        tk.Label(section3_tab, text="Slice 1, System 2").grid(row=4, column=1, sticky=tk.W)
        tk.Label(section3_tab, text="RFOUT").grid(row=5, column=1, sticky=tk.E)
        tk.Label(section3_tab, text="RFIN").grid(row=6, column=1, sticky=tk.E)
        self.sect3_entry = tk.Entry(section3_tab)
        self.sect3_entry.grid(row=5, column=2, sticky=tk.W)
        self.sect3_entry2 = tk.Entry(section3_tab)
        self.sect3_entry2.grid(row=6, column=2, sticky=tk.W)
        
        tk.Label(section3_tab, text="Slice 2, System 1").grid(row=1, column=1, sticky=tk.W)
        tk.Label(section3_tab, text="RFOUT").grid(row=2, column=1, sticky=tk.E)
        tk.Label(section3_tab, text="RFIN").grid(row=3, column=1, sticky=tk.E)
        self.sect3_entry3 = tk.Entry(section3_tab)
        self.sect3_entry3.grid(row=2, column=2, sticky=tk.W)
        self.sect3_entry4 = tk.Entry(section3_tab)
        self.sect3_entry4.grid(row=3, column=2, sticky=tk.W)

        tk.Label(section3_tab, text="Slice 2, System 2").grid(row=7, column=1, sticky=tk.W)
        tk.Label(section3_tab, text="RFOUT").grid(row=8, column=1, sticky=tk.E)
        tk.Label(section3_tab, text="RFIN").grid(row=9, column=1, sticky=tk.E)
        self.sect3_entry5 = tk.Entry(section3_tab)
        self.sect3_entry5.grid(row=8, column=2, sticky=tk.W)
        self.sect3_entry6 = tk.Entry(section3_tab)
        self.sect3_entry6.grid(row=9, column=2, sticky=tk.W)


    def get_files_from_folder(self):
        folder_path = "./"  # Replace with the path to your folder
        files = [file for file in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, file))]
        return files

    def get_npy_files_from_folder(self):
        npy_folder_path = "./"  # Replace with the path to your .npy files folder
        npy_files = [file for file in os.listdir(npy_folder_path) if file.endswith(".npy")]
        return npy_files

if __name__ == "__main__":
    app = kidpy3_GUI()
    app.mainloop()