#!/usr/bin/env python3

import numpy as np
import noise
from save import save
from erosion import EvolutionModel
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
n = np.zeros((mapsize, mapsize))

#micronoise_depth = 0.05

params = {
    "octaves" : int(np.log2(mapsize)),
    "persistence" : 0.5,
    "lacunarity" : 2.,
}

xbase = np.random.randint(65536)
ybase = np.random.randint(65536)

for x in range(mapsize):
    for y in range(mapsize):
        n[x,y] = noise.snoise2(x/scale + xbase, y/scale + ybase, **params)

#micronoise = np.random.rand(mapsize, mapsize)
#nn = np.exp(n*2) + micronoise*micronoise_depth
nn = n*mapsize/5 + mapsize/20

print('Initializing model')
model = EvolutionModel(nn, K=1, m=0.35, d=1, sea_level=0)

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

save(model.dem, 'dem', dtype='>i2')
save(model.lakes, 'lakes', dtype='>i2')
save(model.dirs, 'links', dtype='u1')
save(model.rivers, 'rivers', dtype='>u4')

with open('size', 'w') as sfile:
    sfile.write('{:d}\n{:d}'.format(mapsize, mapsize))

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
    plt.title('Rivers discharge')

    plt.show()
except:
    pass
