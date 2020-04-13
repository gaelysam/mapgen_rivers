#!/usr/bin/env python3

import numpy as np
import zlib
import matplotlib.pyplot as plt

def load_map(name, dtype, shape):
    dtype = np.dtype(dtype)
    with open(name, 'rb') as f:
        data = f.read()
    if len(data) < shape[0]*shape[1]*dtype.itemsize:
        data = zlib.decompress(data)
    return np.frombuffer(data, dtype=dtype).reshape(shape)

shape = np.loadtxt('size', dtype='u4')
n = shape[0] * shape[1]
dem = load_map('dem', '>i2', shape)
lakes = load_map('lakes', '>i2', shape)
rivers = load_map('rivers', '>u4', shape)

plt.subplot(1,3,1)
plt.pcolormesh(dem, cmap='viridis')
plt.gca().set_aspect('equal', 'box')
#plt.colorbar(orientation='horizontal')
plt.title('Raw elevation')

plt.subplot(1,3,2)
plt.pcolormesh(lakes, cmap='viridis')
plt.gca().set_aspect('equal', 'box')
#plt.colorbar(orientation='horizontal')
plt.title('Lake surface elevation')

plt.subplot(1,3,3)
plt.pcolormesh(np.log(rivers), vmin=0, vmax=np.log(n/25), cmap='Blues')
plt.gca().set_aspect('equal', 'box')
#plt.colorbar(orientation='horizontal')
plt.title('Rivers discharge')

plt.show()
