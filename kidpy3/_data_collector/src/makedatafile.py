import h5py
import numpy as np
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