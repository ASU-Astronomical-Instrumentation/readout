# Notes


## rfsoc.py

---------------------------------------------------------------------
### RedisConnection

#### is_Connected:
  - This really shouldn't raise an exception
  1. Redis Connection Error
  2. Redis timeout Error

#### issue_command
  1. Received no response from RFSOC 
  2. Error response from the RFSOC
  3. Key Error
  4. JSON Decode Error
  5. UUID Mismatch, should this even be an exception or used to track system issues

### RFSOC

* RedisConnection.issue_command is the first to error and return None when the RFSOC doesnt reply
* That propogates to for instance: upload bitstream which then sees that the returned value is None
  and then complains itself also returning.

* This should be raised in the RedisConnection class because that prevents currently unnecessary code duplication
  #### __init__
  1. Cascaded exceptions from self.read_config

  #### read_config
  1. ConfigKeyError
  2. ConfigAttributeError
  3. uncaught file not found error from `OmegaConf.load`

  #### Upload bitstream
  1. Fail to upload bitstream
  2. Cascaded exceptions from RedisConnection.issue_command
  
  #### configure hardware
  1. May throw issues access dicts, may have uncaught 
      exceptions COnfigKeyError, ConfigAttributeError
  2. Cascaded exception from RedisConnection.issue_command
  
  #### set_tone_list
  1. Cascaded exceptions from RedisConnection.issue_command
  
  #### get_tone_list
  1. Cascaded exceptions from RedisConnection.issue_command



## data_handler.py
---------------------------------------------------------------------
### RawDataFile
1. Unhandled exception possible when h5py is used to open a non-existent file
2. Unhandled exception possible when h5py trys to create a 
    file without requisite permissions



## UDP2.py
-----------------------------------------------------------------------
I'm not even sure that I want to touch this.

- Still need to handle being unable to bind a socket
- 



[ Notes on the Last Meeting]

I should guard each key I expect to read and 

