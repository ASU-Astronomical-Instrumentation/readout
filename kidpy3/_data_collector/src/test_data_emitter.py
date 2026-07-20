import socket
import numpy as np
import time
import h5py
def start_high_rate_injector(host="127.0.0.1", port=40096):
    # 1. Pre-compute the data to save CPU cycles in the loop
    # Array A: 0 to 1023, Array B: 1023 down to 0
    array_a = np.arange(1024, dtype=np.int32)
    array_b = np.flip(np.arange(1024, dtype=np.int32))

    interleaved = np.zeros(2052, dtype=np.int32)
    interleaved[0:2048:2] = array_a[0:1024]
    interleaved[1:2048:2] = array_b[0:1024]
    packet_data = interleaved.tobytes()

    # 2. Setup Socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Increase buffer size for high-rate local transmission
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)

    interval = 0.002048  # 2.048 ms
    next_tick = time.perf_counter()

    print(f"Broadcasting at 488Hz (every {interval*1000:.3f}ms) to {host}:{port}")
    print("Press Ctrl+C to stop.")

    try:
        count = 0
        while True:
            # Send the pre-computed bytes
            sock.sendto(packet_data, (host, port))

            count += 1
            if count % 488 == 0:
                print(f"Sent {count} packets...")

            # 3. Precise Timing Logic
            next_tick += interval
            sleep_time = next_tick - time.perf_counter()
            if sleep_time > 0:
                time.sleep(sleep_time)
            # If sleep_time is negative, we are lagging behind;
            # we skip the sleep to try and catch up.

    except KeyboardInterrupt:
        print("\nStopping injector...")
    finally:
        sock.close()

if __name__ == "__main__":
    # Lets first create a datafile
    start_high_rate_injector()