#!/usr/bin/env python3

import numpy as np
import noise
from save import save
from erosion import EvolutionModel
import bounds
import os
import sys
import settings

# Always place in this script's parent directory
os.chdir(os.path.dirname(sys.argv[0]))
argc = len(sys.argv)

params = {}

if argc > 1:
	if os.path.isfile(sys.argv[1]):
		params = settings.read_config_file(sys.argv[1])
	else:
		mapsize = int(sys.argv[1])

def get_setting(name, default):
	if name in params:
		return params[name]
	return default

mapsize = int(get_setting('mapsize', 400))
scale = float(get_setting('scale', 200.0))
vscale = float(get_setting('vscale', 200.0))
offset = float(get_setting('offset', 0.0))
persistence = float(get_setting('persistence', 0.5))
lacunarity = float(get_setting('lacunarity', 2.0))

K = float(get_setting('K', 1.0))
m = float(get_setting('m', 0.35))
d = float(get_setting('d', 1.0))
sea_level = float(get_setting('sea_level', 0.0))
flex_radius = float(get_setting('flex_radius', 20.0))

time = float(get_setting('time', 10.0))
niter = int(get_setting('niter', 10))

n = np.zeros((mapsize+1, mapsize+1))

# Set noise parameters
params = {
    "octaves" : int(np.ceil(np.log2(mapsize)))+1,
    "persistence" : persistence,
    "lacunarity" : lacunarity,
}

# Determine noise offset randomly
xbase = np.random.randint(65536)
ybase = np.random.randint(65536)

# Generate the noise
for x in range(mapsize+1):
    for y in range(mapsize+1):
        n[x,y] = noise.snoise2(x/scale + xbase, y/scale + ybase, **params)

nn = n*vscale + offset

# Initialize landscape evolution model
print('Initializing model')
model = EvolutionModel(nn, K=1, m=0.35, d=1, sea_level=0, flex_radius=flex_radius)

dt = time/niter

# Run the model's processes: the order in which the processes are run is arbitrary and could be changed.
print('Initial flow calculation')
model.calculate_flow()

for i in range(niter):
    print('Iteration {:d} of {:d}'.format(i+1, niter))
    print('Diffusion')
    model.diffusion(dt)
    print('Advection')
    model.advection(dt)
    print('Isostatic equilibration')
    model.adjust_isostasy()
    print('Flow calculation')
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
