import numpy as np
import zlib

def save(data, fname, dtype=None):
    if dtype is not None:
        data = data.astype(dtype)

    bin_data = data.tobytes()
    bin_data_comp = zlib.compress(bin_data, 9)
    if len(bin_data_comp) < len(bin_data):
        bin_data = bin_data_comp
    with open(fname, 'wb') as f:
        f.write(bin_data)
