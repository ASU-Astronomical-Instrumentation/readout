import socket
import numpy as np
import time
import h5py
def start_high_rate_injector(host="127.0.0.1", port=40096):
    # 1. Pre-compute the data to save CPU cycles in the loop
    # Array A: 0 to 1023, Array B: 1023 down to 0
    array_a = np.arange(1024, dtype=np.int32)
    array_b = np.flip(np.arange(1024, dtype=np.int32))

    interleaved = np.empty(2048, dtype=np.int32)
    interleaved[0::2] = array_a
    interleaved[1::2] = array_b
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
    with h5py.File("test_dataset.h5", 'w') as fd:
        print("Creating dataset")
        n_sample = 0
        chunk_size = 488
        n_fftbins = 1024
        fd.create_group("global_data")
        fd.create_dataset("dimension/n_sample",
                          (1,),
                          maxshape=(1,),
                          dtype=h5py.h5t.STD_U64LE,
        )
        adc_i = fd.create_dataset(
            "time_ordered_data/adc_i",
            (n_fftbins, n_sample),
            chunks=(n_fftbins, chunk_size),
            maxshape=(n_fftbins, None),
            dtype=h5py.h5t.STD_I32LE,
        )
        adc_q = fd.create_dataset(
            "time_ordered_data/adc_q",
            (n_fftbins, n_sample),
            chunks=(n_fftbins, chunk_size),
            maxshape=(n_fftbins, None),
            dtype=h5py.h5t.STD_I32LE,
        )

        timestamp = fd.create_dataset(
            "time_ordered_data/timestamp",
            (n_sample,),
            chunks=(chunk_size,),
            maxshape=(None,),
            dtype=h5py.h5t.IEEE_F64LE,
        )
        pkt_idx = fd.create_dataset(
            "time_ordered_data/pkt_idx",
            (n_sample,),
            chunks=(chunk_size,),
            maxshape=(None,),
            dtype=h5py.h5t.STD_U32LE)
        pps = fd.create_dataset(
            "time_ordered_data/pps",
            (0,),
            chunks=(488,),
            maxshape=(None,),
            dtype=h5py.h5t.STD_U8LE,
        )
    # start_high_rate_injector()