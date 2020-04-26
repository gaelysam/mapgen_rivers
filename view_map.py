#!/usr/bin/env python3

import numpy as np
import zlib
import matplotlib.colors as mcol
import matplotlib.pyplot as plt

def view_map(dem, lakes, rivers):
    plt.subplot(1,3,1)
    plt.pcolormesh(dem, cmap='viridis')
    plt.gca().set_aspect('equal', 'box')
    plt.colorbar(orientation='horizontal')
    plt.title('Raw elevation')

    plt.subplot(1,3,2)
    plt.pcolormesh(lakes, cmap='viridis')
    plt.gca().set_aspect('equal', 'box')
    plt.colorbar(orientation='horizontal')
    plt.title('Lake surface elevation')

    plt.subplot(1,3,3)
    plt.pcolormesh(rivers, cmap='Blues', norm=mcol.LogNorm())
    plt.gca().set_aspect('equal', 'box')
    plt.colorbar(orientation='horizontal')
    plt.title('Rivers flux')

    plt.show()

if __name__ == "__main__":
    import sys
    import os
    if len(sys.argv) > 1:
        os.chdir(sys.argv[1])

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
    rivers = load_map('rivers', '>u4', shape)

    view_map(dem, lakes, rivers)
