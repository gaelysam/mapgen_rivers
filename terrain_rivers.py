#!/usr/bin/env python3

import numpy as np
import noise
from save import save
from erosion import EvolutionModel
import bounds
import os
import sys

# Always place in this script's parent directory
os.chdir(os.path.dirname(sys.argv[0]))
argc = len(sys.argv)

if argc > 1:
	mapsize = int(sys.argv[1])
else:
	mapsize = 401

scale = (mapsize-1) / 2
n = np.zeros((mapsize, mapsize))

# Set noise parameters
params = {
    "octaves" : int(np.ceil(np.log2(mapsize-1)))+1,
    "persistence" : 0.5,
    "lacunarity" : 2.,
}

# Determine noise offset randomly
xbase = np.random.randint(65536)
ybase = np.random.randint(65536)

# Generate the noise
for x in range(mapsize):
    for y in range(mapsize):
        n[x,y] = noise.snoise2(x/scale + xbase, y/scale + ybase, **params)

nn = n*mapsize/5 + mapsize/20

# Initialize landscape evolution model
print('Initializing model')
model = EvolutionModel(nn, K=1, m=0.35, d=1, sea_level=0)

# Run the model's processes: the order in which the processes are run is arbitrary and could be changed.
print('Flow calculation 1')
model.calculate_flow()

print('Advection 1')
model.advection(2)

print('Isostatic equilibration 1')
model.adjust_isostasy()

print('Flow calculation 2')
model.calculate_flow()

print('Diffusion')
model.diffusion(4)

print('Advection 2')
model.advection(2)

print('Isostatic equilibration 2')
model.adjust_isostasy()

print('Flow calculation 3')
model.calculate_flow()

print('Done')

# Twist the grid
bx, by = bounds.make_bounds(model.dirs, model.rivers)
ox, oy = bounds.twist(bx, by, bounds.get_fixed(model.dirs))

# Convert offset in 8-bits
offset_x = np.clip(np.floor(ox * 256), -128, 127)
offset_y = np.clip(np.floor(oy * 256), -128, 127)

# Save the files
save(model.dem, 'dem', dtype='>i2')
save(model.lakes, 'lakes', dtype='>i2')
save(np.abs(bx), 'bounds_x', dtype='>i4')
save(np.abs(by), 'bounds_y', dtype='>i4')
save(offset_x, 'offset_x', dtype='i1')
save(offset_y, 'offset_y', dtype='i1')

save(model.rivers, 'rivers', dtype='>u4')

with open('size', 'w') as sfile:
    sfile.write('{:d}\n{:d}'.format(mapsize, mapsize))

# Display the map if matplotlib is found
try:
    import matplotlib.pyplot as plt

    plt.subplot(2,2,1)
    plt.pcolormesh(nn, cmap='viridis')
    plt.gca().set_aspect('equal', 'box')
    #plt.colorbar(orientation='horizontal')
    plt.title('Raw elevation')

    plt.subplot(2,2,2)
    plt.pcolormesh(model.lakes, cmap='viridis')
    plt.gca().set_aspect('equal', 'box')
    #plt.colorbar(orientation='horizontal')
    plt.title('Lake surface elevation')

    plt.subplot(2,2,3)
    plt.pcolormesh(model.dem, cmap='viridis')
    plt.gca().set_aspect('equal', 'box')
    #plt.colorbar(orientation='horizontal')
    plt.title('Elevation after advection')

    plt.subplot(2,2,4)
    plt.pcolormesh(model.rivers, vmin=0, vmax=mapsize**2/25, cmap='Blues')
    plt.gca().set_aspect('equal', 'box')
    #plt.colorbar(orientation='horizontal')
    plt.title('Rivers flux')

    plt.show()
except:
    pass
