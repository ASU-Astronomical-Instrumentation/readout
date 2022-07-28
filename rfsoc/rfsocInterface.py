"""
@author Cody Roberson, Adrian Sinclair, Ryan Stephenson, Philip Mauskopf
@date 2022-06-09
@description Handles interfacing with hardware on the RFSOC through
the XILILX PYNQ framework

@revisons:
    2022-06-09
    - Merge changes from fast-bram-design_asu-fixed-phil-adrian-cody-GOLDEN_RECOMPILED.ipynb
    - Added ROOT user permissions check
    2022-06-15
    - Completed conversion from notebook.
    - Modified bitstream management such that the bitstream loaded can be passed as a parameter.
"""
#user check since we can't run without root priviliges
import getpass
if getpass.getuser() != "root":
    print("rfsocInterface.py: root priviliges are required, please run as root.") 
    exit()

import os
from pynq import Overlay
from pynq import Xlnk
from pynq import MMIO
import xrfclk
import xrfdc
import struct
from time import sleep
from matplotlib import pyplot as plt
import numpy as np
import ipywidgets as ipw
from ipywidgets import interact, interactive, fixed, interact_manual
from scipy import signal


class rfsocInterface:
    def __init__(self):
        print("init")
        self.firmware = None
        #self.bram_ADCI = None
        #self.bram_ADCQ = None
        #self.pfbIQ = None
        #self.ddc_snap = None
        #self.accum_snap = None
        self.selectedBitstream = None

    def uploadOverlay(self, bitstream="./single_chan_4eth_v8p2.bit"):
        # FIRMWARE UPLOAD
        self.firmware = Overlay(bitstream,ignore_version=True)
        self.selectedBitstream = bitstream
        # INITIALIZING PLLs
        clksrc = 409.6 # MHz
        xrfclk.set_all_ref_clks(clksrc)
        lofreq = 1000.000 # [MHz]
        rf_data_conv = self.firmware.usp_rf_data_converter_0
        rf_data_conv.adc_tiles[0].blocks[0].MixerSettings['Freq']=lofreq
        rf_data_conv.dac_tiles[1].blocks[3].MixerSettings['Freq']=lofreq
        rf_data_conv.adc_tiles[0].blocks[0].UpdateEvent(xrfdc.EVENT_MIXER)
        rf_data_conv.dac_tiles[1].blocks[3].UpdateEvent(xrfdc.EVENT_MIXER)
        print("Firmware uploaded and pll set")
        return 0
    
    def getFirmwareObjects(self, bitstream="./single_chan_4eth_v8p2.bit"):
        self.firmware = Overlay(bitstream, ignore_version=True,download=False)
        self.bram_ADCI = self.firmware.ADC_I.BRAM_SNAP_0
        self.bram_ADCQ = self.firmware.ADC_Q.BRAM_SNAP_0
        self.pfbIQ = self.firmware.PFB_SNAP_SYNC.BRAM_SNAPIII_0
        self.ddc_snap = self.firmware.DDC_SNAP_SYNC.BRAM_SNAPIII_0
        self.accum_snap = self.firmware.ACCUM_SNAP_SYNC.BRAM_SNAPIII_0

        return self.firmware

    def initRegs(self):
        if self.firmware==None:
          print("Overlay must be uploaded first")
          return -1
        
        # SET ETHERNET IPS and MACS
        def ethRegsPortWrite(eth_regs,
                             src_ip_int32   = int("c0a80335",16), # defaults
                             dst_ip_int32   = int("c0a80328",16),
                             src_mac0_int32 = int("deadbeef",16),
                             src_mac1_int16 = int("feed",16),
                             dst_mac0_int16 = int("0991",16),     # 00:e0:4c:68:09:91 
                             dst_mac1_int32 = int("00e04c68",16)):
            eth_regs.write( 0x00, src_mac0_int32) 
            eth_regs.write( 0x04, (dst_mac0_int16<<16) + src_mac1_int16)
            eth_regs.write( 0x08, dst_mac1_int32)
            eth_regs.write( 0x0c, src_ip_int32)
            eth_regs.write( 0x10, dst_ip_int32)
            
        ethRegsPortWrite(self.firmware.eth_wrap.eth_regs_port0, src_ip_int32=int("c0a80332",16))
        ethRegsPortWrite(self.firmware.eth_wrap.eth_regs_port1, src_ip_int32=int("c0a80333",16))
        ethRegsPortWrite(self.firmware.eth_wrap.eth_regs_port2, src_ip_int32=int("c0a80334",16))
        ethRegsPortWrite(self.firmware.eth_wrap.eth_regs_port3, src_ip_int32=int("c0a80335",16))
        
        eth_delay_reg = self.firmware.eth_wrap.eth_delay # programmable delay for eth byte shift
        data_in_mux = self.firmware.eth_wrap.data_in_mux
        ###############################
        # Ethernet Delay Lines  
        ###############################
        eth_delay_reg.write(0x00, -22 + (4<<16))#-22 + (4<<16)) #-22 + (4<<16))#44 + (4<<16)) # data output from eth buffer delay/ input to eth buffer delay <<16 delay
        eth_delay_reg.write(0x08, 0) # ethernet start pulse out delay
        ###############################
        # Data MUX
        ###############################
        data_in_mux.write( 0x00, 1) # coffee when 0, data when 1
        data_in_mux.write( 0x08, (509) + ((8189)<<16) ) # 
        
    def set_dd_shift(shift):
        pass


    def norm_wave(self, ts, max_amp=2**15-1):
        """
         Re-configure generated data values to fit LUT
        """
        Imax = max(abs(ts.real))
        Qmax = max(abs(ts.imag))
        norm = max(abs(ts))
        dacI = ((ts.real/norm)*max_amp).astype("int16")
        dacQ = ((ts.imag/norm)*max_amp).astype("int16")
        return dacI, dacQ
        
    def genWaveform(self, freq_list, vna = False, verbose=False):
        """
        Takes a list of specified frequencies and generates....stuff and things, then 
        uploads to the bram.
        
        params
            freq_list: np.array
                list of tones to generate [Hz]
            verbose: bool
                enable / disable printing (and or) plotting of data
        """
        #####################################################
        # HARDCODED LUT PARAMS
        #####################################################
        addr_size=18   # address bit width
        channels= 2    # data points per memory address for DAC
        fs = 1024e6    # sampling rate of D/A, FPGA fabric = fs/2
        C=2            # decimation factor
        data_p = channels*2**(addr_size) # length of timestream or length of LUT+1
        
        #####################################################
        #  SET FREQ for LUT
        #####################################################
        if vna:
          N = 1000 # number of tones to make
          #freqs = -1*C*np.linspace(-250.0e6, 250.0e6,N) # equally spaced tones
          freqs_up = 1*C*np.linspace(-251e6,-1e6, N//2)
          freqs_lw = 1*C*np.linspace(2.15e6,252.15e6,N//2)
          freqs = np.append(freqs_up,freqs_lw)
          #freqs = freqs_up
        else:
          freqs = C*freq_list # equally spaced tones
        phases = np.random.uniform(-np.pi,np.pi,len(freqs))

        ######################################################
        # DAC Params
        ######################################################
        A = 2**15-1 # 16 bit D/A, expecting signed values.
        freq_res = fs/data_p # Hz
        fftbin_bw = 500e3 # Hz for effective bandwidth of 512MHz/1024 point fft on adc
        print(freq_res)
        
        ######################################################
        # GENERATE LUT WAVEFORM FROM FREQ LIST
        ######################################################
        freqs = np.round(freqs/(freq_res))*freq_res
        print("{} Frequencies Generated:".format(len(freqs)))
        print(freqs/C*1e-6)
        delta = np.zeros(data_p,dtype="complex") # empty array of deltas
        fft_bin_nums=np.zeros(len(freqs),dtype=int) # array of all dac bin index
        for i in range(len(freqs)):
            bin_num = np.round((freqs[i]/freq_res)).astype('int')
            fft_bin_nums[i]=(np.round((freqs[i]/fftbin_bw/C)).astype('int'))*C
            delta[bin_num] = np.exp(1j*phases[i]) 
        ts = np.fft.ifft(delta)

        # GENERATE DDC WAVEFORM FROM BEAT FREQS
        f_fft_bin = fft_bin_nums*fftbin_bw
        f_beat = (freqs/C - f_fft_bin/C)
        
        if verbose:
            print("\nBeat Frequencies:")
            print(f_beat)
            print(freqs/C)

        ###########
        # new DDC
        ###########
        wave_ddc = np.zeros( int(data_p), dtype="complex") # empty array of deltas
        delta_ddc = np.zeros( shape=(len(freqs),2**9), dtype="complex") # empty array of deltas
        beat_ddc = np.zeros(shape=(len(freqs),2**9), dtype="complex")
        bin_num_ddc = np.round(f_beat*2/freq_res) # factor of 2 for half a bin width
        
        print("bin num ddc "+str(bin_num_ddc))

        for i in range(len(freqs)): 
            delta_ddc[i,int(bin_num_ddc[i])] = np.exp(-1j*phases[i])
            beat_ddc[i] = np.conj(np.fft.ifft(delta_ddc[i]))
            
        for i in range(1024):
            if (i<len(freqs)):
                wave_ddc[i::1024] = beat_ddc[i]
            else:
                wave_ddc[i::1024] = 0
        
        dacI, dacQ = self.norm_wave(ts)
        ddcI, ddcQ = self.norm_wave(wave_ddc, max_amp=(2**13)-1)
        return dacI, dacQ, ddcI, ddcQ, freqs
    
    def load_DAC(self, wave_real, wave_imag):
        base_addr_DAC_I = 0x0400000000
        base_addr_DAC_Q = 0x0400100000
        mem_size = 262144*4 # 32 bit address slots
        mmio_bramI = MMIO(base_addr_DAC_I,mem_size)
        mmio_bramQ = MMIO(base_addr_DAC_Q,mem_size)
        I0, I1 = wave_real[0::2], wave_real[1::2]
        Q0, Q1 = wave_imag[0::2], wave_imag[1::2]
        dataI = ((np.int32(Q1) << 16) + I1).astype("int32")
        dataQ = ((np.int32(Q0) << 16) + I0).astype("int32")
        mmio_bramI.array[0:262144] = dataI[0:262144]
        mmio_bramQ.array[0:262144] = dataQ[0:262144]
        print("DAC waveform uploaded to AXI BRAM")
        return

    def load_DDS(self, wave_real, wave_imag):

        base_addr_DDS_I = 0x0080000000
        base_addr_DDS_Q = 0x0080100000
        mem_size = 262144*4 # 32 bit address slots
        mmio_bramI = MMIO(base_addr_DDS_I,mem_size)
        mmio_bramQ = MMIO(base_addr_DDS_Q,mem_size)
        I0, I1 = wave_real[0::2], wave_real[1::2]
        Q0, Q1 = wave_imag[0::2], wave_imag[1::2]
        dataI = ((np.int32(I1) << 16) + I0).astype("int32")
        dataQ = ((np.int32(Q1) << 16) + Q0).astype("int32")
        mmio_bramI.array[0:262144] = dataI[0:262144]
        mmio_bramQ.array[0:262144] = dataQ[0:262144]
        print("DDC waveform uploaded to AXI BRAM")
        return
 
    def load_bin_list(self, freqs):
        bin_list = np.int64( np.round(freqs/1e6) )
        print("bin_list:"+str(bin_list))
        # DSP REGS
        dsp_regs = self.firmware.dsp_regs_0
        # 0x00 -  fft_shift[9 downto 0], load_bins[22 downto 12], lut_counter_rst[11 downto 11] 
        # 0x04 -  bin_num[9 downto 0]
        # 0x08 -  accum_len[23 downto 0], accum_rst[24 downto 24], sync_in[26 downto 26] (start dac)
        # 0x0c -  dds_shift[8 downto 0]
        
        # initialization 
        sync_in = 2**26
        accum_rst = 2**24  # (active low)
        accum_length = (2**19)-1
        ################################################
        # Load DDC bins
        ################################################
        offs=0
        
        # only write tones to bin list
        for addr in range(1024):
            if addr<(len(bin_list)):
                print("addr = {}, bin# = {}".format(addr, bin_list[addr]))
                dsp_regs.write(0x04,int(bin_list[addr]))
                dsp_regs.write(0x00, ((addr<<1)+1)<<12)
                dsp_regs.write(0x00, 0)
            else:
                dsp_regs.write(0x04,0)
                dsp_regs.write(0x00, ((addr<<1)+1)<<12)
                dsp_regs.write(0x00, 0)
        return

    def load_waveform_into_mem(self, freqs, dac_r,dac_i,dds_r,dds_i):
        #######################################################
        # Load configured LUT values into FPGA memory
        #######################################################
        
        # Arming DDC Waveform
        ########################
        dsp_regs = self.firmware.dsp_regs_0
        # 0x00 -  fft_shift[9 downto 0], load_bins[22 downto 12], lut_counter_rst[11 downto 11] 
        # 0x04 -  bin_num[9 downto 0]
        # 0x08 -  accum_len[23 downto 0], accum_rst[24 downto 24], sync_in[26 downto 26] (start dac)
        # 0x0c -  dds_shift[8 downto 0]
        # initialization  
        sync_in = 2**26
        accum_rst = 2**24  # (active rising edge)
        accum_length = (2**19)-1 # (2**18)-1
        
        fft_shift=0
        if len(freqs)<400:
            fft_shift = 2**9-1
        else:
            fft_shift = 2**5-1 #2**2-1
        
        # WRITING TO DDS SHIFT
        dsp_regs.write(0x0c,262)
        dsp_regs.write(0x08,accum_length)
        
        # reset DAC/DDS counter
        dsp_regs.write(0x00, 2**11) # reset dac/dds counter
        dsp_regs.write(0x00, 0) # reset dac/dds counter
        dsp_regs.write(0x08,accum_length | accum_rst)
        
        self.load_DAC(dac_r,dac_i)
        self.load_DDS(dds_r,dds_i)
        sleep(.5)
        dsp_regs.write(0x00, fft_shift) # set fft shift
        ########################
        dsp_regs.write(0x08, accum_length | sync_in)
        sleep(0.5)
        dsp_regs.write(0x08, accum_length | accum_rst | sync_in)
        return 0

    def get_snap_data(self, mux_sel):
        # WIDE BRAM
        axi_wide = self.firmware.axi_wide_ctrl# 0x0 max count, 0x8 capture rising edge trigger
        max_count = 32768
        #mux_sel = 3
        axi_wide.write(0x08, mux_sel<<1) # mux select 0-adc, 1-pfb, 2-ddc, 3-accum
        axi_wide.write(0x00, max_count - 16) # -4 to account for extra delay in write counter state machine
        axi_wide.write(0x08, mux_sel<<1 | 0)
        axi_wide.write(0x08, mux_sel<<1 | 1)
        axi_wide.write(0x08, mux_sel<<1 | 0)
        base_addr_wide = 0x00_A007_0000
        mmio_wide_bram = MMIO(base_addr_wide,max_count)
        wide_data = mmio_wide_bram.array[0:8192]# max/4, bram depth*word_bits/32bits
        if mux_sel==0:
            #adc parsing
            up0, lw0 = np.int16(wide_data[0::4] >> 16), np.int16(wide_data[0::4] & 0x0000ffff)
            up1, lw1 = np.int16(wide_data[1::4] >> 16), np.int16(wide_data[1::4] & 0x0000ffff)
            I = np.zeros(4096)
            Q = np.zeros(4096)
            Q[0::2] = lw0
            Q[1::2] = up0
            I[0::2] = lw1
            I[1::2] = up1
        elif mux_sel==1:
            # pfb
            chunk0 = (np.uint64(wide_data[1::4]) << np.uint64(32)) + np.uint64(wide_data[0::4])
            chunk1 = (np.uint64(wide_data[2::4]) << np.uint64(32)) + np.uint64(wide_data[1::4])
            q0 = np.int64((chunk0 & 0x000000000003ffff)<<np.uint64(46))/2**32
            i0 = np.int64(((chunk0>>18) & 0x000000000003ffff)<<np.uint64(46))/2**32
            q1 = np.int64(((chunk1>>4)  & 0x000000000003ffff)<<np.uint64(46))/2**32
            i1 = np.int64(((chunk1>>22)  & 0x000000000003ffff)<<np.uint64(46))/2**32
            I = np.zeros(4096)
            Q = np.zeros(4096)
            Q[0::2] = q0
            Q[1::2] = q1
            I[0::2] = i0
            I[1::2] = i1
        elif mux_sel==2:
            # ddc
            chunk0 = (np.uint64(wide_data[1::4]) << np.uint64(32)) + np.uint64(wide_data[0::4])
            chunk1 = (np.uint64(wide_data[2::4]) << np.uint64(32)) + np.uint64(wide_data[1::4])
            q0 = np.int64((chunk0 & 0x00000000000fffff)<<np.uint64(45))/2**32
            i0 = np.int64(((chunk0>>19) & 0x00000000000fffff)<<np.uint64(45))/2**32
            q1 = np.int64(((chunk1>>6)  & 0x00000000000fffff)<<np.uint64(45))/2**32
            i1 = np.int64(((chunk1>>25)  & 0x00000000000fffff)<<np.uint64(45))/2**32
            I = np.zeros(4096)
            Q = np.zeros(4096)
            Q[0::2] = q0
            Q[1::2] = q1
            I[0::2] = i0
            I[1::2] = i1
        elif mux_sel==3:
            # accum
            q0 = (np.int32(wide_data[1::4])).astype("float")
            i0 = (np.int32(wide_data[0::4])).astype("float")
            q1 = (np.int32(wide_data[3::4])).astype("float")
            i1 = (np.int32(wide_data[2::4])).astype("float")
            I = np.zeros(4096)
            Q = np.zeros(4096)
            Q[0::2] = q0
            Q[1::2] = q1
            I[0::2] = i0
            I[1::2] = i1    
        return I, Q
    
    def get_adc_data(self):
        I, Q = self.get_snap_data(0)
        return I,Q

    def get_pfb_data(self):
        I, Q = self.get_snap_data(1)
        return I, Q

    def get_ddc_data(self):
        I, Q = self.get_snap_data(2)
        return I, Q 

    def get_accum_data(self):
        I, Q = self.get_snap_data(3)
        return I, Q  

    def writeWaveform(self, waveform, vna=False, verbose=False):
        """
        writeWaveform: Exports a given waveform to the DAC's on board. This is the
        primary function that should be exposed to the user.

        waveform : numpy.array
            List of Desired Frequencies in Hz units. Note that users must account for this unit 
            and use 10eN notation. eg: 10e6 for 10 MHz

            Example usage:
                writeWaveform(np.array([10e6, 13e6, 16e6, 200e6]))
        vna : boolean
            If enabled, sets the waveform to be 1000 equally spaced tones from -256 to +256 MHz
            or 500MHz Bandwidth

        verbose : boolean
            (DEPRECATED) -> Enabled various print statements, most of which have been removed.
        """
        LUT_I, LUT_Q, DDS_I, DDS_Q, freqs = self.genWaveform(waveform, vna=vna, verbose=verbose)
        self.load_bin_list(freqs)
        self.load_waveform_into_mem(freqs, LUT_I, LUT_Q, DDS_I, DDS_Q)
        np.save("freqs.npy",freqs)

    def set_NCLO(self, lofreq):
        rf_data_conv = self.firmware.usp_rf_data_converter_0
        rf_data_conv.adc_tiles[0].blocks[0].MixerSettings['Freq']=lofreq
        rf_data_conv.dac_tiles[1].blocks[3].MixerSettings['Freq']=lofreq
        rf_data_conv.adc_tiles[0].blocks[0].UpdateEvent(xrfdc.EVENT_MIXER)
        rf_data_conv.dac_tiles[1].blocks[3].UpdateEvent(xrfdc.EVENT_MIXER)

    def sweep(self, f_center, freqs):
        """
        
        """
        N_steps =  500 #
        tone_diff = np.diff(freqs)[0]/1e6 # MHz
        flo_step = tone_diff/N_steps
        flo_start = f_center - tone_diff/2. #256
        flo_stop =  f_center + tone_diff/2. #256

        flos = np.arange(flo_start, flo_stop, flo_step)

        def temp(lofreq):
            self.set_NCLO(lofreq)
            # self.set_ValonLO function here
            # Read values and trash initial read, suspecting linear delay is cause..
            Naccums = 5
            I, Q = [], []
            for i in range(Naccums):
                It, Qt = self.get_accum_data()
                I.append(It)
                Q.append(Qt)
            I = np.array(I)
            Q = np.array(Q)
            Imed = np.median(I,axis=0)
            Qmed = np.median(Q,axis=0)

            Z = Imed + 1j*Qmed
            Z = Z[0:len(freqs)]

            print(".", end="")

            return Z

        sweep_Z = np.array([
            temp(lofreq)
            for lofreq in flos
        ])

        f = np.array([flos*1e6 + ftone for ftone in freqs]).flatten()
        sweep_Z_f = sweep_Z.T.flatten()

        ## SAVE f and sweep_Z_f TO LOCAL FILES
        # SHOULD BE ABLE TO SAVE TARG OR VNA
        # WITH TIMESTAMP

        return (f, sweep_Z_f)
    
    def vnaSweep(self, f_center=600):
        """
        vnaSweep: perform a stepped frequency sweep centered at f_center and save result as s21.npy file

        f_center: center frequency for sweep in [MHz]

        """
        freqs = np.load("freqs.npy")
        f, sweep_Z_f = self.sweep(f_center, freqs)
        np.save("s21.npy", np.array((f, sweep_Z_f)))
        print("s21.npy saved.")

