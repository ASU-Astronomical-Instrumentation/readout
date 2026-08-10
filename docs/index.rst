.. mKID Readout Library documentation master file, created by
   sphinx-quickstart on Tue Feb 20 14:23:43 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

=====================
MKID Readout Library 
=====================

Background
-----------
The ZCU111 RFSoC is a system on a chip featuring an FPGA and an Arm Cortex-A53 Quad-Core processor with built in ADC's and DAC's.
The OS is a variant of Ubuntu which allows for the use of python and other conventional software tools.
There is also an AMD (Xilinx) provided framework called PYNQ which allows users to interact with the RFSoC FPGA using Jupyter Notebooks.

This library is seperated into two parts:

   1. The kidpy3 folder which contains the host (flight computer) side code.

   2. The rfsoc folder which contains the command listener and executor code for the RFSoC.



.. toctree::
   :maxdepth: 3
   :caption: Documentation:

   getting_started
   pc_rfsoc_control


.. toctree::
   :maxdepth: 3
   :caption: API Reference:

   modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
