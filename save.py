import numpy as np

def save(data, fname, dtype=None):
    if dtype is not None:
        data = data.astype(dtype)

    with open(fname, 'wb') as f:
        f.write(data.tobytes())
