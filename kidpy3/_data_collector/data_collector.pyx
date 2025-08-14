cdef extern from "src/data_collector.h":
    void c_say_hi()

def say_hello():
    c_say_hi()
