import sys
import importlib as _importlib
import logging

__version__ = '3.0.0'


submodules = [
    'science'
]

# Check Python version
if sys.version_info.major == 3 and sys.version_info.minor >= 8:
    pass
else:
    raise Exception("Python 3.8 or newer is required.")

# Module Imports
from .data_handler import *
from .rfsoc import *
from .udp2 import *

__all__ = submodules + ['__version__']

def __dir__():
    return __all__

def __getattr__(name):
    if name in submodules:
        return _importlib.import_module(f'kidpy3.{name}')
    else:
        try:
            return globals()[name]
        except KeyError:
            raise AttributeError(
                f"Module 'scipy' has no attribute '{name}'"
            )


__LOGFMT = "%(asctime)s|%(levelname)s|%(filename)s|%(lineno)d|%(funcName)s| %(message)s"
logging.basicConfig(format=__LOGFMT, level=logging.INFO)
logger = logging.getLogger(__name__)
logh = logging.FileHandler("./kidpy_debug.log")
logger.addHandler(logh)
logh.setFormatter(logging.Formatter(__LOGFMT))
