==================================
Controlling the RFSOC using Redis
==================================

Background
-----------

The ZCU111 RFSoC utilizes the AMD (Xilinx) provided framework called PYNQ
to control the RFSoC. PYNQ is a Python-based framework that allows users to control the
RFSoC including the FPGA firmware using Python. This library provides a way to control
the RFSoC using Redis, a popular in-memory data structure store, which can be used as a
database, cache, and message broker. Software written in Python and running on the RFSoC utilizes redis to 
communicate with the host computer. This document details the redis messages that this library utilizes on the backend.


Command Message Format
-----------------------

