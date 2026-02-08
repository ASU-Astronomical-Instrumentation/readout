import os
import socket
import numpy as np

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    arr = np.arange(0, 2048, dtype=np.int32)
    payload = arr.astype('>i4').tobytes()
    try:
        s.sendto(payload, ("127.0.0.1", 4096))
    except KeyboardInterrupt:
        return
if __name__ == "__main__":
    main()