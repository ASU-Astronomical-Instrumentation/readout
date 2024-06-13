# Kidpy3
import sys
from . import kp3Exceptions

# Check Python version
if sys.version_info.major == 3 and sys.version_info.minor >= 6:
    pass
else:
    raise kp3Exceptions.VersionException()

# Modify the module imports
from .rfsoc import RFSOC
from . import data_handler
from .udp2 import libcapture
from . import ifslice
from . import measurements
from .udp2 import udpcap

# from kidpy3.data_handler import RawDataFile


# Set up logging
import logging

__LOGFMT = "%(asctime)s|%(levelname)s|%(filename)s|%(lineno)d|%(funcName)s| %(message)s"
logging.basicConfig(format=__LOGFMT, level=logging.INFO)
logger = logging.getLogger(__name__)
logh = logging.FileHandler("./kidpy_debug.log")
logger.addHandler(logh)
logh.setFormatter(logging.Formatter(__LOGFMT))
