import numpy as np
import scipy.ndimage as im
from .rivermapper import flow

def advection(dem, dirs, rivers, time, K=1, m=0.5, sea_level=0):
    """
    Simulate erosion by rivers.
    This models erosion as an upstream advection of elevations ("erosion waves").
    Advection speed depends on water flux and parameters:

    v = K * flux^m
    """

    dirs = dirs.copy()
    dirs[0,:] = 0
    dirs[-1,:] = 0
    dirs[:,0] = 0
    dirs[:,-1] = 0

    adv_time = 1 / (K*rivers**m) # For every pixel, calculate the time an "erosion wave" will need to cross it.
    dem = np.maximum(dem, sea_level)
    dem_new = np.zeros(dem.shape)

    for y in range(dirs.shape[0]):
        for x in range(dirs.shape[1]):
            # Elevations propagate upstream, so for every pixel we seek the downstream pixel whose erosion wave just reached the current pixel.
            # This means summing the advection times downstream until we reach the erosion time.
            x0, y0 = x, y
            x1, y1 = x, y
            remaining = time
            while True:
                # Move one pixel downstream
                flow_dir = dirs[y0,x0]
                if flow_dir == 0:
                    remaining = 0
                    break
                elif flow_dir == 1:
                    y1 += 1
                elif flow_dir == 2:
                    x1 += 1
                elif flow_dir == 3:
                    y1 -= 1
                elif flow_dir == 4:
                    x1 -= 1

                if remaining <= adv_time[y0,x0]: # Time is over, we found it.
                    break
                remaining -= adv_time[y0,x0]
                x0, y0 = x1, y1

            c = remaining / adv_time[y0,x0]
            dem_new[y,x] = c*dem[y1,x1] + (1-c)*dem[y0,x0] # If between 2 pixels, perform linear interpolation.

    return np.minimum(dem, dem_new)

def diffusion(dem, time, d=1):
    radius = d * time**.5
    return im.gaussian_filter(dem, radius, mode='reflect') # Diffusive erosion is a simple Gaussian blur

class EvolutionModel:
    def __init__(self, dem, K=1, m=0.5, d=1, sea_level=0, flow=False, flex_radius=100):
        self.dem = dem
        #self.bedrock = dem
        self.K = K
        self.m = m
        self.d = d
        self.sea_level = sea_level
        self.flex_radius = flex_radius
        self.define_isostasy()
        if flow:
            self.calculate_flow()
        else:
            self.lakes = dem
            self.dirs = np.zeros(dem.shape, dtype='u1')
            self.rivers = np.zeros(dem.shape, dtype='u4')
            self.flow_uptodate = False

    def calculate_flow(self):
        self.dirs, self.lakes, self.rivers = flow(self.dem)
        self.flow_uptodate = True

    def advection(self, time):
        dem = advection(self.lakes, self.dirs, self.rivers, time, K=self.K, m=self.m, sea_level=self.sea_level)
        self.dem = np.minimum(dem, self.dem)
        self.flow_uptodate = False

    def diffusion(self, time):
        self.dem = diffusion(self.dem, time, d=self.d)
        self.flow_uptodate = False

    def define_isostasy(self):
        self.ref_isostasy = im.gaussian_filter(self.dem, self.flex_radius, mode='reflect') # Define a blurred version of the DEM that will be considered as the reference isostatic elevation.

    def adjust_isostasy(self, rate=1):
        isostasy = im.gaussian_filter(self.dem, self.flex_radius, mode='reflect') # Calculate blurred DEM
        correction = (self.ref_isostasy - isostasy) * rate # Compare it with the reference isostasy
        self.dem = self.dem + correction # Adjust
