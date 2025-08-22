import os
import socket
import numpy as np

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    payload = np.arange(0, 1024)

    try:
        s.sendto(payload.tobytes(), ("127.0.0.1", 4096))
    except KeyboardInterrupt:
        return
if __name__ == "__main__":
    main()