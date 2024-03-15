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

**Commands to the rfsoc are passed from host to redis to rfsoc**


.. code-block:: json

   {
         "command": "command_name",
         "data": {
              "arg1": "value1",
              "arg2": "value2",
              "argN" : "valueN"
         }
   }


**Replies from the rfsoc are passed from rfsoc to redis to host following this format**


.. code-block:: json

   {
        "status": "OK or ERROR",
        "error" : "Error information if status is ERROR",
        "data": {
            "arg1": "value1",
            "arg2": "value2",
            "argN" : "valueN"
         }
   }


Under the Hood
--------------

In python, the built-in Dicts are passed to and from the json library using the json.dumps() and json.loads() functions.