# Kidpy3
import sys
from . import kp3Exceptions

# Check Python version
if sys.version_info.major == 3 and sys.version_info.minor >= 6:
    pass
else:
    raise kp3Exceptions.VersionException()

from rfsoc import rfsoc
from onr_ifslice import onr_ifslice
from valon import valon