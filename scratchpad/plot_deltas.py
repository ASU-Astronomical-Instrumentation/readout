import numpy as np
import matplotlib.pyplot as plt
import h5py


def main():
    with h5py.File("test_dataset.h5", 'r') as fd:
        print("Reading data")

        adc_i: np.ndarray = fd["time_ordered_data/adc_i"][...]
        adc_q: np.ndarray = fd["time_ordered_data/adc_q"][...]
        indx: np.ndarray = fd["time_ordered_data/pkt_idx"][...]
        ts: np.ndarray = fd["time_ordered_data/timestamp"][...]

        # print(adc_i.shape)
        # print(adc_q.shape)
        # print(indx.shape)

        # print(ts.shape)

        ts_delta = np.diff(ts)
        indx_delta = np.diff(indx)

        print("AVG Δ Timestamp", np.average(ts_delta[1:]))
        print("MED Δ Timestamp", np.median(ts_delta[1:]))
        print("AVE Δ Index: ", np.average(indx_delta[1:]))
        print("MED Δ Index: ", np.median(indx_delta[1:]))

        plt.close("all")
        plt.figure(figsize=(12, 6))
        plt.plot(ts_delta[1:])
        plt.xlabel("Sample")
        plt.ylabel("Δ Timestamp (Seconds)")
        plt.savefig("ts_delta.png")

        plt.figure(figsize=(12, 6))
        plt.stem(indx_delta[1:])
        plt.xlabel("Sample")
        plt.ylabel("Δ Packet Counter")
        plt.savefig("indx_delta.png")
        plt.show()



if __name__ == "__main__":
    main()
