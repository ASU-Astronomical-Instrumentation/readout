from .rfsoc import new_config
from omegaconf import OmegaConf
import sys

def gen_config():
    """Generates a new configuration file. This should be callable from the command line."""
    if len(sys.argv) > 1:
        file = sys.argv[1]
        c = new_config()
        OmegaConf.save(c, file)
    else:
        print("Usage: kp3-mkconfig <path/to/file.yml>")
