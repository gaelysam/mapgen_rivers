#!/usr/bin/env python3

import numpy as np
from noise import snoise2, snoise3
import os
import sys

import terrainlib

class noisemap:
    def __init__(self, X, Y, scale=0.01, vscale=1.0, tscale=1.0, offset=0.0, log=None, xbase=None, ybase=None, **params):
        # Determine noise offset randomly
        if xbase is None:
            xbase = np.random.randint(8192)-4096
        if ybase is None:
            ybase = np.random.randint(8192)-4096
        self.xbase = xbase
        self.ybase = ybase
        self.X = X
        self.Y = Y
        self.scale = scale
        if log:
            vscale /= offset
        self.vscale = vscale
        self.tscale = tscale
        self.offset = offset
        self.log = log
        self.params = params

    def get2d(self):
        n = np.zeros((self.X, self.Y))
        for x in range(self.X):
            for y in range(self.Y):
                n[x,y] = snoise2(x/self.scale + self.xbase, y/self.scale + self.ybase, **self.params)

        if self.log:
            return np.exp(n*self.vscale) * self.offset
        else:
            return n*self.vscale + self.offset

    def get3d(self, t=0):
        t /= self.tscale
        n = np.zeros((self.X, self.Y))
        for x in range(self.X):
            for y in range(self.Y):
                n[x,y] = snoise3(x/self.scale + self.xbase, y/self.scale + self.ybase, t, **self.params)

        if self.log:
            return np.exp(n*self.vscale) * self.offset
        else:
            return n*self.vscale + self.offset

### PARSE COMMAND-LINE ARGUMENTS
argc = len(sys.argv)

config_file = 'terrain_default.conf'
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

K = float(get_setting('K', 0.5))
m = float(get_setting('m', 0.5))
d = float(get_setting('d', 0.5))
sea_level = float(get_setting('sea_level', 0.0))
sea_level_variations = float(get_setting('sea_level_variations', 0.0))
sea_level_variations_time = float(get_setting('sea_level_variations_time', 1.0))
flex_radius = float(get_setting('flex_radius', 20.0))
flow_method = get_setting('flow_method', 'semirandom')

time = float(get_setting('time', 10.0))
niter = int(get_setting('niter', 10))

### MAKE INITIAL TOPOGRAPHY
n = np.zeros((mapsize+1, mapsize+1))

# Set noise parameters
params = {
    "offset" : offset,
    "vscale" : vscale,
    "scale" : scale,
    "octaves" : int(np.ceil(np.log2(mapsize)))+1,
    "persistence" : persistence,
    "lacunarity" : lacunarity,
}

params_sealevel = {
    "octaves" : 1,
    "persistence" : 1,
    "lacunarity" : 2,
}

params_K = {
    "offset" : K,
    "vscale" : K,
    "scale" : 400,
    "octaves" : 1,
    "persistence" : 0.5,
    "lacunarity" : 2,
    "log" : True,
}

params_m = {
    "offset" : m,
    "vscale" : m*0.5,
    "scale" : 400,
    "octaves" : 1,
    "persistence" : 0.5,
    "lacunarity" : 2,
    "log" : True,
}

if sea_level_variations != 0.0:
    sea_ybase = np.random.randint(8192)-4096
    sea_level_ref = snoise2(time * (1-1/niter) / sea_level_variations, sea_ybase, **params_sealevel) * sea_level_variations
    params['offset'] -= (sea_level_ref + sea_level)

n = noisemap(mapsize+1, mapsize+1, **params).get2d()
m_map = noisemap(mapsize+1, mapsize+1, **params_m).get2d()
K_map = noisemap(mapsize+1, mapsize+1, **params_K).get2d()

### COMPUTE LANDSCAPE EVOLUTION
# Initialize landscape evolution model
print('Initializing model')
model = terrainlib.EvolutionModel(n, K=K_map, m=m_map, d=d, sea_level=sea_level, flex_radius=flex_radius, flow_method=flow_method)
terrainlib.update(model.dem, model.lakes, t=5, sea_level=model.sea_level, title='Initializing...')

dt = time/niter

# Run the model's processes: the order in which the processes are run is arbitrary and could be changed.

for i in range(niter):
    disp_niter = 'Iteration {:d} of {:d}...'.format(i+1, niter)
    if sea_level_variations != 0:
        model.sea_level = snoise2((i*dt)/sea_level_variations_time, sea_ybase, **params_sealevel) * sea_level_variations - sea_level_ref
    terrainlib.update(model.dem, model.lakes, sea_level=model.sea_level, title=disp_niter)
    print(disp_niter)
    print('Diffusion')
    model.diffusion(dt)
    print('Flow calculation')
    model.calculate_flow()
    terrainlib.update(model.dem, model.lakes, sea_level=model.sea_level, title=disp_niter)
    print('Advection')
    model.advection(dt)
    print('Isostatic equilibration')
    model.adjust_isostasy()

print('Last flow calculation')
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
