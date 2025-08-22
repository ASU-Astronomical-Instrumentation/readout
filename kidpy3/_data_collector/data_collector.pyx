cdef extern from "src/data_collector.h":
    void c_say_hi()

def say_hello():
    """
    prints "Hello world!\n" to stdout
    :return:
    """
    c_say_hi()
