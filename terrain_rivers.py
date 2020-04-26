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
	mapsize = 400

scale = mapsize / 2
n = np.zeros((mapsize+1, mapsize+1))

# Set noise parameters
params = {
    "octaves" : int(np.ceil(np.log2(mapsize)))+1,
    "persistence" : 0.5,
    "lacunarity" : 2.,
}

# Determine noise offset randomly
xbase = np.random.randint(65536)
ybase = np.random.randint(65536)

# Generate the noise
for x in range(mapsize+1):
    for y in range(mapsize+1):
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
offset_x, offset_y = bounds.twist(bx, by, bounds.get_fixed(model.dirs))

# Convert offset in 8-bits
offset_x = np.clip(np.floor(offset_x * 256), -128, 127)
offset_y = np.clip(np.floor(offset_y * 256), -128, 127)

if not os.path.isdir('data'):
    os.mkdir('data')
os.chdir('data')
# Save the files
save(model.dem, 'dem', dtype='>i2')
save(model.lakes, 'lakes', dtype='>i2')
save(offset_x, 'offset_x', dtype='i1')
save(offset_y, 'offset_y', dtype='i1')

save(model.dirs, 'dirs', dtype='u1')
save(model.rivers, 'rivers', dtype='>u4')

with open('size', 'w') as sfile:
    sfile.write('{:d}\n{:d}'.format(mapsize+1, mapsize+1))

# Display the map if matplotlib is found
try:
    from view_map import view_map
    view_map(model.dem, model.lakes, model.rivers)
except:
    pass
