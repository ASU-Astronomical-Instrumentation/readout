"""
@author Cody Roberson, Adrian Sinclair, Ryan Stephenson, Philip Mauskopf
@date 2022-06-09
@description Handles interfacing with hardware on the RFSOC through
the XILILX PYNQ framework

@revisons:
    2022-06-09
    - Merge changes from fast-bram-design_asu-fixed-phil-adrian-cody-GOLDEN_RECOMPILED.ipynb
    - Added ROOT user permissions check

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
        self.bram_ADCI = None
        self.bram_ADCQ = None
        self.pfbIQ = None
        self.ddc_snap = None
        self.accum_snap = None

    def uploadOverlay(self):
        # FIRMWARE UPLOAD
        self.firmware = Overlay("/bitstreams/blast_1.0.bit",ignore_version=True)
        # INITIALIZING LMK04208 CLOCK
        xrfclk.set_all_ref_clks(409.6) # MHz
        print("Firmware uploaded and pll set")
        return 0
    
    def getFirmwareObjects(self):
        self.firmware = Overlay("/bitstreams/blast_1.0.bit",ignore_version=True,download=False)
        return self.firmware

    def initRegs(self):
        if self.firmware==None:
          print("Overlay must be uploaded first")
          return -1
        ########################3
        # Configure udp ip and mac
        ##########################
        dst_mac_reg = self.firmware.IP_MAC_gpio_hier.dst_mac # 48 bits, offset 0x00 bottom 32bits, 0x08 top 16 bits
        src_mac_reg = self.firmware.IP_MAC_gpio_hier.src_mac # 48 bits, offset 0x00 bottom 32bits, 0x08 top 16 bits
        ip_reg = self.firmware.IP_MAC_gpio_hier.ip # offset 0x00 src ip, offset 0x08 dst ip
        eth_delay_reg = self.firmware.eth_delay # programmable delay for eth byte shift
        data_in_mux = self.firmware.data_in_mux
        # setting ips
        src_ip_int32 = int("c0a80329",16)
        dst_ip_int32 = int("c0a80328",16)
        src_mac0_int32 = int("deadbeef",16)
        src_mac1_int16 = int("feed",16)
        dst_mac0_int32 = int("5d092bb0",16) #  startech dongle 80:3f:5d:09:6b:1d
        dst_mac1_int16 = int("803f",16) 

        # write values
        ip_reg.write( 0x00, src_ip_int32) 
        ip_reg.write( 0x08, dst_ip_int32)
        dst_mac_reg.write( 0x00, dst_mac0_int32)
        dst_mac_reg.write( 0x08, dst_mac1_int16)
        src_mac_reg.write( 0x00, src_mac0_int32)
        src_mac_reg.write( 0x08, src_mac1_int16)
        ###############################
        # Ethernet Delay Lines  
        ###############################
        eth_delay_reg.write(0x00, 37 + (4<<16))#44 + (4<<16)) # data output from eth buffer delay/ input to eth buffer delay <<16 delay
        eth_delay_reg.write(0x08, 3) # start pulse out delay
        ###############################
        # Data MUX
        ###############################
        data_in_mux.write( 0x00, 1) # coffee when 0, data when 1
        data_in_mux.write( 0x08, (509) + ((8189)<<16) ) # ethernet max write count and max read count
        
        self.bram_ADC_I = self.firmware.ADC_I.BRAM_SNAP_0
        self.bram_ADC_Q = self.firmware.ADC_Q.BRAM_SNAP_0
        self.pfbIQ = self.firmware.PFB_SNAP_SYNC.BRAM_SNAPIII_0
        self.ddc_snap = self.firmware.DDC_SNAP_SYNC.BRAM_SNAPIII_0
        self.accum_snap = self.firmware.ACCUM_SNAP_SYNC.BRAM_SNAPIII_0

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
           
    def surfsUpDude(self, freq_list, vna = False, verbose=False):
        """
        surfsUpDude Takes a list of specified frequencies and generates....gnarly lookup tables and 
        ditigal down conversion broah. 
        Then we'll have totally ripped waves bruh, for shreddin the gnar.

        params
            freqlist: np.array
                list of tones to generate
            vna: bool
                When falst, uploads given frequency list, otherwise upload 1k tones from
                -256 Mhz to 256 MHz
            verbose: bool
                enable / disable printing (and or) plotting of data

        """
        if self.firmware==None:
          print("Overlay must be uploaded first")
          return -1
            #BRAM driver code for bram v0.42



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
          freqs_up = 1*C*np.linspace(-251e6,-1e6, N/2)
          freqs_lw = 1*C*np.linspace(2.25e6,252.25e6,N/2)
          freqs = np.append(freqs_up,freqs_lw)
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

        ###########
        # new DDC
        ###########
        wave_ddc = np.zeros( int(data_p), dtype="complex") # empty array of deltas
        delta_ddc = np.zeros( shape=(len(freqs),2**9), dtype="complex") # empty array of deltas
        beat_ddc = np.zeros(shape=(len(freqs),2**9), dtype="complex")
        bin_num_ddc = np.round(f_beat*2/freq_res) # factor of 2 for half a bin width


        for i in range(len(freqs)):
            delta_ddc[i,int(bin_num_ddc[i])] = np.exp(-1j*phases[i])
            beat_ddc[i] = np.conj(np.fft.ifft(delta_ddc[i]))

        for i in range(1024):
            if (i<len(freqs)):
                wave_ddc[i::1024] = beat_ddc[i]
            else:
                wave_ddc[i::1024] = 0 # beat_ddc[0]


        dacI, dacQ = norm_wave(ts)
        ddcI, ddcQ = norm_wave(wave_ddc, max_amp=(2**13)-1)

        
        return dacI, dacQ, ddcI, ddcQ, freqs

    def load_DAC(self, wave_real, wave_imag):
        """
        load_dac
            Load waveform via bram controller into BRAM
        """
        # get base address from overlay
        base_addr_DAC_I = int(self.firmware.ip_dict['DAC_I/axi_bram_ctrl_0']['parameters']['C_S_AXI_BASEADDR'], 16)
        base_addr_DAC_Q = int(self.firmware.ip_dict['DAC_Q/axi_bram_ctrl_0']['parameters']['C_S_AXI_BASEADDR'], 16)
        mem_size = 262144*4 # 32 bit address slots
        mmio_bramI = MMIO(base_addr_DAC_I,mem_size)
        mmio_bramQ = MMIO(base_addr_DAC_Q,mem_size)
        I0, I1 = wave_real[0::2], wave_real[1::2]
        Q0, Q1 = wave_imag[0::2], wave_imag[1::2]
        dataI = ((np.int32(I1) << 16) + I0).astype("int32")
        dataQ = ((np.int32(Q1) << 16) + Q0).astype("int32")
        mmio_bramI.array[0:262144] = dataI[0:262144] # half of data
        mmio_bramQ.array[0:262144] = dataQ[0:262144]
        print("DAC waveform uploaded to AXI BRAM")
        return 

    def load_DDS(self, wave_real, wave_imag):
        """
        load dds
            Load dds waveform via bram controller into bram
        """
        base_addr_DDS_I = int(self.firmware.ip_dict['DDC_I/axi_bram_ctrl_0']['parameters']['C_S_AXI_BASEADDR'], 16) 
        base_addr_DDS_Q = int(self.firmware.ip_dict['DDC_Q/axi_bram_ctrl_0']['parameters']['C_S_AXI_BASEADDR'], 16)
        mem_size = 262144*4 # 32 bit address slots
        mmio_bramI = MMIO(base_addr_DDS_I,mem_size)
        mmio_bramQ = MMIO(base_addr_DDS_Q,mem_size)
        I0, I1 = wave_real[0::2], wave_real[1::2]
        Q0, Q1 = wave_imag[0::2], wave_imag[1::2]
        dataI = ((np.int32(I1) << 16) + I0).astype("int32")
        dataQ = ((np.int32(Q1) << 16) + Q0).astype("int32")
        mmio_bramI.array[0:262144] = dataI[0:262144] # half of data
        mmio_bramQ.array[0:262144] = dataQ[0:262144]
        print("DDC waveform uploaded to AXI BRAM")
        return

    def load_bin_list(self, freqs):
        bin_list = np.int64( np.round(freqs/1e6) )
        fft_shift_and_load_bins = self.firmware.gpio1.axi_gpio_0 # 0x00 fft shift, 0x08 load bins
        accum_and_bin_idx = self.firmware.gpio2.axi_gpio_0 # 0x00 bins, 0x08 0-23 accum len, 24 accum rst, 25 sync in
        # initialization
        sync_in = 2**26
        accum_rst = 2**24  # (active low)
        accum_length = (2**19)-1

        ################################################
        # Load DDC bins
        ################################################
        #offs=60
        offs=20#12

        # only write tones to bin list
        for addr in range(1024):
             if ((offs-1)<addr<((offs)+len(bin_list))):
                 print("addr = {}, bin# = {}".format(addr, bin_list[addr-offs]))
                 accum_and_bin_idx.write(0x00, int(bin_list[addr-offs])) #110 # write bin for address single address
                 fft_shift_and_load_bins.write(0x08,(addr<<1)+1) # enable we
                 fft_shift_and_load_bins.write(0x08,0) # disable we
             else:
                 accum_and_bin_idx.write(0x00,0)#0) #110 # write bin for address single address
                 fft_shift_and_load_bins.write(0x08,(addr<<1)+1) # enable we
                 fft_shift_and_load_bins.write(0x08,0) # disable we

        return

    def load_waveform_into_mem(self, freqs, dac_r,dac_i,dds_r,dds_i):
        #######################################################
        # Load configured LUT values into FPGA memory
        #######################################################

        # Arming DDC Waveform
        ########################
        # initialization


        sync_in = 2**26
        accum_rst = 2**24  # (active redge)
        accum_length = (2**19)-1 # (2**18)-1

        fft_shift=0
        if len(freqs)<400:
            fft_shift = 1*((2**9)-1) #(2**7)-1 # CHANGED FOR NEW GPIO
        else:
            fft_shift = 1*((2**5)-1) #(2**7)-1 # CHANGED FOR NEW GPIO


        fft_shift_and_load_bins = self.firmware.gpio1.axi_gpio_0
        dds_shift=self.firmware.gpio3.axi_gpio_0 # DDS SHIFT offset = 0x00, 0x08 is open
        dds_shift.write(0x00,234) # WRITING TO DDS SHIFT
        accum_and_bin_idx = self.firmware.gpio2.axi_gpio_0 # 0x00 bins, 0x08 0b-23b accum len, 24b accum rst, 26b sync in
        accum_and_bin_idx.write(0x08,1*accum_length) #100

        # accum reset low then high
        fft_shift_and_load_bins.write(0x00,2**11) # reset DAC/DDS counter

        accum_and_bin_idx.write(0x08,1*accum_length+0*sync_in+1*accum_rst) # 101

        self.load_DAC(dac_r,dac_i)
        self.load_DDS(dds_r,dds_i)
        sleep(.5)
        fft_shift_and_load_bins.write(0x00, fft_shift+2**10) # enable DAC/DDS counter
        accum_and_bin_idx.write(0x08,1*accum_length+1*sync_in+0*accum_rst) # 110 -- STARTS DSP FIRMWARE
        sleep(0.5)
        accum_and_bin_idx.write(0x08,1*accum_length+1*sync_in+1*accum_rst) #111

        return 0 

    def __get_adc_data_helper(self, snap):
        snap.write(0x04,0)       #
        snap.write(0x04,2**31)   # toggling sync clear
        snap.write(0x04,2**29)   #
        d = np.zeros(2**11)    # bram data

        for i in range(2**11):
            snap.write(0x00,i<<(32-11)) # write address space to read
            for j in range(1):
                snap.write(0x04,j<<19)
                data = snap.read(0x08)
                d[i*1+j]= data

        snap_data = np.array(d).astype("int32")
        snap_data_0 = ((snap_data >> 16).astype("int16"))#.astype('float') # decoding concatenated values
        snap_data_1 = ((snap_data & (2**(16)-1)).astype("int16"))#.astype('float')
        d2 = np.zeros(2*2**11)# bram data
        d2[0::2]=snap_data_1
        d2[1::2]=snap_data_0
        return d2

    def get_adc_data(self):
        Q = self.__get_adc_data(self.bram_ADCQ)
        I = self.__get_adc_data(self.bram_ADCI)
        return I,Q

    def get_pfb_data(self, snap): # make sure to toggle sync (gpio) first
        snap.write(0x04,0)       #
        snap.write(0x04,2**31)   # toggling sync clear
        snap.write(0x04,2**29)       #
        d = np.zeros(4*2**11)# bram data

        for i in range(2**11):
            snap.write(0x00,i<<(32-11)) # write address space to read
            for j in range(4):
                snap.write(0x04,j<<19)
                data = snap.read(0x08)
                d[i*4+j]= data

        snap_data = np.array(d).astype("uint32")
        snap_data=snap_data<<14
        return snap_data


    def get_ddc_data(self, snap):
        snap.write(0x04,0)
        snap.write(0x04,2**31)# toggling sync clear
        snap.write(0x04,2**29)#
        d = np.zeros(4*2**11)# bram data

        for i in range(2**11):
            snap.write(0x00,i<<(32-11)) # write address space to read
            for j in range(4):
                snap.write(0x04,j<<19)
                data = snap.read(0x08)
                d[i*4+j]= data
        snap_data = np.array(d).astype("uint32")

        return snap_data<<13
