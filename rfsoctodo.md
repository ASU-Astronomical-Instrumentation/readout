TODO in the RFSOC Folder
Lets find out where all of the exceptions that can occur...

- remove code to that attempts multiple times to establish a connection to redis.
- Lets transition to using a service deamon instead as god intended.
- Some exceptions should occur and crash the program --> get restarted by systemd.
- Some exceptions should be an error reply that lets the user know something wasn't setup as expected
  - one example is upload bitstream. This should be checked prior to any command being accepted;
    not crash, and reported back to the kidpy3 lib where it then raises an exception on the host.


MAIN()
======
- [] if 'command' not in COMMAND_DICT, that should raise a key error exception.
  This is caught but not returned to the user and the current text is misleading
- [] on JSONDecode error, this should also be an error returned to the user
- [] Same with KEYERROr
- [] Bug where I try to use command[...] on line 208 AFTER an exception caused by being unable
  to perform the very same operation occurs. Just reply to the user that it's not going to happen.

RedisConnection:
================
- [] remove the loop based attempt to reconnect and instead log the error to a file



------
# Logging to a file and limiting file size...
https://docs.python.org/3/library/logging.handlers.html#logging.handlers.RotatingFileHandler

Simply use a Rotating File Handler.
  - `maxBytes` is max size
  - `backupCount` should be at least 1; allows for the creation of N backup logs that are created / renamed after rollover.
