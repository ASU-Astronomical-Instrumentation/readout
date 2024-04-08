=========================================
Info on Controlling the RFSOC using Redis
=========================================


Under the Hood
--------------

A command is initiated in kidpy3 through the RFSOC class. This command and it's arguments are packaged as a DICT object and then converted into
a json object and sent to the redis server using its pub-sub functionality. Any RFSOC's listening to the redis server (and channel)
will receive the command. If the command is valid and the arguments are correct, the RFSOC will execute the command and reply.
``redisControl.py`` contains a dictionary of all the commands that can be executed by the RFSoC and the corresponding function that should be called. 
If the ``command_name`` doesn't match the dictionary, the RFSoC will reply with an error message.


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



Command Reference
-----------------

.. list-table:: config_hardware
   :widths: 20 20 70
   :header-rows: 1
   
   * - Arguments
     - Type
     - Description

   * - tbd
     - tbd
     - tbd

   * - tbd
     - tbd
     - tbd

.. list-table:: upload_bitstream
   :widths: 20 20 70
   :header-rows: 1

   * - Arguments
     - Type
     - Description

   * - tbd
     - tbd
     - tbd

   * - tbd
     - tbd
     - tbd

.. list-table:: set_tone_list
   :widths: 20 20 70
   :header-rows: 1

   * - Arguments
     - Type
     - Description

   * - tbd
     - tbd
     - tbd

   * - tbd
     - tbd
     - tbd

.. list-table:: get_tone_list
   :widths: 20 20 70
   :header-rows: 1

   * - Arguments
     - Type
     - Description

   * - tbd
     - tbd
     - tbd

   * - tbd
     - tbd
     - tbd

.. list-table:: set_amplitude_list
   :widths: 20 20 70
   :header-rows: 1

   * - Arguments
     - Type
     - Description

   * - tbd
     - tbd
     - tbd

   * - tbd
     - tbd
     - tbd

.. list-table:: get_amplitude_list
   :widths: 20 20 70
   :header-rows: 1

   * - Arguments
     - Type
     - Description

   * - tbd
     - tbd
     - tbd

   * - tbd
     - tbd
     - tbd

.. list-table:: blank_cmd_here
   :widths: 20 20 70
   :header-rows: 1

   * - Arguments
     - Type
     - Description

   * - tbd
     - tbd
     - tbd

   * - tbd
     - tbd
     - tbd


Example Command String
^^^^^^^^^^^^^^^^^^^^^^

**package command**

.. code-block:: python

      def some_function()
         cmddict = { 
         "command": "config_hardware", 
         "args": { 
            "srcip" : "192.168.2.10", 
            "dstip" : "192.168.40.51"}
         }
         cmdstr = json.dumps(cmddict)
         return cmdstr



**resulting string**

::
   
   '{"command": "config_hardware", "args": {"srcip": "192.168.2.10", "dstip": "192.168.40.51"}}'

This will appear in the redis server as a string like this (some characters are escaped with the \\ character):

::

   "{\"command\": \"config_hardware\", \"args\": {\"srcip\": \"192.168.2.10\", \"dstip\": \"192.168.40.51\"}}"
