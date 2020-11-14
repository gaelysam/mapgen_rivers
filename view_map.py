#!/usr/bin/env python3

import numpy as np
import zlib
import sys
import os

from terrainlib import stats, plot

scale = 1
if len(sys.argv) > 1:
    os.chdir(sys.argv[1])
if len(sys.argv) > 2:
    scale = int(sys.argv[2])

def load_map(name, dtype, shape):
    dtype = np.dtype(dtype)
    with open(name, 'rb') as f:
        data = f.read()
        if len(data) < shape[0]*shape[1]*dtype.itemsize:
            data = zlib.decompress(data)
        return np.frombuffer(data, dtype=dtype).reshape(shape)

shape = np.loadtxt('size', dtype='u4')
dem = load_map('dem', '>i2', shape)
lakes = load_map('lakes', '>i2', shape)

stats(dem, lakes, scale=scale)
plot(dem, lakes, scale=scale)
