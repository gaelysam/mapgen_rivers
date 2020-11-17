#!/usr/bin/env python3

import numpy as np
import noise
import os
import sys

import terrainlib

### PARSE COMMAND-LINE ARGUMENTS
argc = len(sys.argv)

config_file = 'terrain.conf'
output_dir = 'river_data'
params_from_args = {}
i = 1 # Index of arguments
j = 1 # Number of 'orphan' arguments (the ones that are not preceded by '--something')
while i < argc:
    arg = sys.argv[i]
    if arg[:2] == '--':
        pname = arg[2:]
        v = None
        split = pname.split('=', maxsplit=1)
        if len(split) == 2:
            pname, v = split
            i += 1
        elif i+1 < argc:
            v = sys.argv[i+1]
            i += 2

        if v is not None:
            if pname == 'config':
                config_file = v
            elif pname == 'output':
                output_dir = v
            else:
                params_from_args[pname] = v
    else:
        if j == 1:
            config_file = arg
        elif j == 2:
            output_dir = arg
        i += 1
        j += 1

print(config_file, output_dir)

params = terrainlib.read_config_file(config_file)
params.update(params_from_args) # Params given from args prevail against conf file

### READ SETTINGS
def get_setting(name, default):
    if name in params:
        return params[name]
    return default

mapsize = int(get_setting('mapsize', 1000))
scale = float(get_setting('scale', 400.0))
vscale = float(get_setting('vscale', 300.0))
offset = float(get_setting('offset', 0.0))
persistence = float(get_setting('persistence', 0.6))
lacunarity = float(get_setting('lacunarity', 2.0))

K = float(get_setting('K', 1.0))
m = float(get_setting('m', 0.35))
d = float(get_setting('d', 0.2))
sea_level = float(get_setting('sea_level', 0.0))
flex_radius = float(get_setting('flex_radius', 20.0))

time = float(get_setting('time', 10.0))
niter = int(get_setting('niter', 10))

### MAKE INITIAL TOPOGRAPHY
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

### COMPUTE LANDSCAPE EVOLUTION
# Initialize landscape evolution model
print('Initializing model')
model = terrainlib.EvolutionModel(nn, K=1, m=0.35, d=1, sea_level=0, flex_radius=flex_radius)
terrainlib.update(model.dem, model.lakes, t=5, title='Initializing...')

dt = time/niter

# Run the model's processes: the order in which the processes are run is arbitrary and could be changed.
print('Initial flow calculation')
model.calculate_flow()

for i in range(niter):
    disp_niter = 'Iteration {:d} of {:d}...'.format(i+1, niter)
    terrainlib.update(model.dem, model.lakes, title=disp_niter)
    print(disp_niter)
    print('Diffusion')
    model.diffusion(dt)
    print('Advection')
    model.advection(dt)
    print('Isostatic equilibration')
    model.adjust_isostasy()
    print('Flow calculation')
    model.calculate_flow()

print('Done!')

# Twist the grid
bx, by = terrainlib.make_bounds(model.dirs, model.rivers)
offset_x, offset_y = terrainlib.twist(bx, by, terrainlib.get_fixed(model.dirs))

# Convert offset in 8-bits
offset_x = np.clip(np.floor(offset_x * 256), -128, 127)
offset_y = np.clip(np.floor(offset_y * 256), -128, 127)

### SAVE OUTPUT
if not os.path.isdir(output_dir):
    os.mkdir(output_dir)
os.chdir(output_dir)
# Save the files
terrainlib.save(model.dem, 'dem', dtype='>i2')
terrainlib.save(model.lakes, 'lakes', dtype='>i2')
terrainlib.save(offset_x, 'offset_x', dtype='i1')
terrainlib.save(offset_y, 'offset_y', dtype='i1')

terrainlib.save(model.dirs, 'dirs', dtype='u1')
terrainlib.save(model.rivers, 'rivers', dtype='>u4')

with open('size', 'w') as sfile:
    sfile.write('{:d}\n{:d}'.format(mapsize+1, mapsize+1))

terrainlib.stats(model.dem, model.lakes)
print()
print('Grid is ready for use!')
terrainlib.plot(model.dem, model.lakes, title='Final grid, ready for use!')
