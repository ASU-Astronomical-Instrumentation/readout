"""
Exceptions will be raised. Let them come, we will face them boldly with honor and courage
"""

__all__ = [
    "PythonVersionError",
    "RedisConnectionError",
    "MissingConfigError",
    "ConfigFileNotFound",
    "CommandTimeoutError"
]


class PythonVersionError(Exception):
    """
    This library uses language features that may not be available prior to 3.8. Notably, 3.8 is EOL. 
    """
    def __init__(
        self,
        message="\n\n\033[0;31mKIDPY3 Requires Python Version 3.10 or Later\033[0m\n",
    ):
        self.message = message
        super().__init__(self.message)


class RedisConnectionError(Exception):
    """
    It's possible that the redis server is down and we can't issue commands if that's the case. 
    """
    def __init__(self, message) -> None:
        self.message = message
        super().__init__(self.message)


class MissingConfigError(Exception):
    """
    The RFSOC class reads key value pairs from a user provided config. If a config is missing, well, that's an error 
    and needs to be handled.
    """
    def __init__(self, message = "Expected a key to be present in config, however it was not found.") -> None:
        self.message = message
        super().__init__(self.message)
 
class ConfigFileNotFound(Exception):
    """
    """
    def __init__(self, message = "Was provided a path to a config file which does not exist") -> None:
        self.message = message
        super().__init__(self.message)

class CommandTimeoutError(Exception):
    """
    """
    def __init__(self, message = "Expected a reply from the RFSOC but received none. Did it crash?") -> None:
        self.message = message
        super().__init__(self.message)
