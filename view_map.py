#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt

shape = np.loadtxt('size', dtype='u4')
n = shape[0] * shape[1]
dem = np.fromfile('dem', dtype='>i2').reshape(shape)
lakes = np.fromfile('lakes', dtype='>i2').reshape(shape)
rivers = np.fromfile('rivers', dtype='>u4').reshape(shape)

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
