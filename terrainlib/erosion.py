import numpy as np
import scipy.ndimage as im
import scipy.signal as si
from .rivermapper import flow

def advection(dem, dirs, rivers, time, K=1, m=0.5, sea_level=0):
    """
    Simulate erosion by rivers.
    This models erosion as an upstream advection of elevations ("erosion waves").
    Advection speed depends on water flux and parameters:

    v = K * flux^m
    """

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

    return dem_new

second_derivative_matrix = np.array([
    [0., 0.25, 0.],
    [0.25,-1., 0.25],
    [0., 0.25, 0.],
])

diff_max = 1.0

def diffusion(dem, time, d=1.0):
    if isinstance(d, np.ndarray):
        dmax = d.max()
    else:
        dmax = d
    diff = time * dmax
    print(diff)
    niter = int(diff//diff_max) + 1
    ddiff = d * (time / niter)

    #print('{:d} iterations'.format(niter))
    for i in range(niter):
        dem[1:-1,1:-1] += si.convolve2d(dem, second_derivative_matrix, mode='valid') * ddiff
        #print('iteration {:d}'.format(i+1))

    return dem
    #return im.gaussian_filter(dem, radius, mode='reflect') # Diffusive erosion is a simple Gaussian blur

class EvolutionModel:
    def __init__(self, dem, K=1, m=0.5, d=1, sea_level=0, flow=False, flex_radius=100, flow_method='semirandom'):
        self.dem = dem
        #self.bedrock = dem
        self.K = K
        self.m = m
        if isinstance(d, np.ndarray):
            self.d = d[1:-1,1:-1]
        else:
            self.d = d
        self.sea_level = sea_level
        self.flex_radius = flex_radius
        self.define_isostasy()
        self.flow_method = flow_method
        #set_flow_method(flow_method)
        if flow:
            self.calculate_flow()
        else:
            self.lakes = dem
            self.dirs = np.zeros(dem.shape, dtype=int)
            self.rivers = np.zeros(dem.shape, dtype=int)
            self.flow_uptodate = False

    def calculate_flow(self):
        self.dirs, self.lakes, self.rivers = flow(self.dem, method=self.flow_method)
        self.flow_uptodate = True

    def advection(self, time):
        dem = advection(np.maximum(self.dem, self.lakes), self.dirs, self.rivers, time, K=self.K, m=self.m, sea_level=self.sea_level)
        self.dem = np.minimum(dem, self.dem)
        self.flow_uptodate = False

    def diffusion(self, time):
        self.dem = diffusion(self.dem, time, d=self.d)
        self.flow_uptodate = False

    def define_isostasy(self, dem=None):
        if dem is None:
            dem = self.dem
        self.ref_isostasy = im.gaussian_filter(dem, self.flex_radius, mode='reflect') # Define a blurred version of the DEM that will be considered as the reference isostatic elevation.

    def adjust_isostasy(self, rate=1):
        isostasy = im.gaussian_filter(self.dem, self.flex_radius, mode='reflect') # Calculate blurred DEM
        correction = (self.ref_isostasy - isostasy) * rate # Compare it with the reference isostasy
        self.dem = self.dem + correction # Adjust
