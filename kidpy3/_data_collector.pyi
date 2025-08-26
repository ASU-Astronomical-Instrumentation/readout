def say_hello() -> None:
    """
    Prints out a nice message
    :return: None
    """
    ...
def collect_data(filename: str, ip_addr: str, port: int) -> int:
    """
    Collects streaming data from the RFSoC and saves it to the specified hdf5 file.
    This is a wrapper around the cython function.
    :param filename: String containing a filename.
    :param ip_addr: String containing an ip address.
    :param port: Integer containing a port number. This will be truncated to 16 bits.
    :return: Returns 0 on success, negative numbers on failure.

    Note: The condition result=-2 will probably occur every time the child process is killed.
    """
    ...