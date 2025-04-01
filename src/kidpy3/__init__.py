import sys
from .kp3Exceptions import *
if sys.version_info.minor < 10 or sys.version_info.major < 3:
    raise PythonVersionError
from .data_handler import RawDataFile
from .rfsoc import *
from .udp2 import capture, capture_packets
from . import hardware
from . import measure
