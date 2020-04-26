import numpy as np
import heapq
import sys

# Conventions:
# 1 = South (+Y)
# 2 = East  (+X)
# 3 = North (-Y)
# 4 = West  (-X)

sys.setrecursionlimit(65536)

neighbours_dirs = np.array([
    [0,1,0],
    [2,0,4],
    [0,3,0],
], dtype='u1')

neighbours_pattern = neighbours_dirs > 0

def flow_dirs_lakes(dem, random=0):
    """
    Calculates flow direction in D4 (4 choices) for every pixel of the DEM
    Also returns an array of lake elevation
    """

    (Y, X) = dem.shape

    dem_margin = np.zeros((Y+2, X+2)) # We need a margin of one pixel at every edge, to prevent crashes when scanning the neighbour pixels on the borders
    dem_margin[1:-1,1:-1] = dem
    if random > 0:
        dem_margin += np.random.random(dem_margin.shape) * random

    # Initialize: list map borders
    borders = []

    for x in range(1,X+1):
        dem_north = dem_margin[1,x]
        borders.append((dem_north, dem_north, 1, x))
        dem_south = dem_margin[Y,x]
        borders.append((dem_south, dem_south, Y, x))

    for y in range(2,Y):
        dem_west = dem_margin[y,1]
        borders.append((dem_west, dem_west, y, 1))
        dem_east = dem_margin[y,X]
        borders.append((dem_east, dem_east, y, X))

    # Make a binary heap
    heapq.heapify(borders)

    dirs = np.zeros((Y+2, X+2), dtype='u1')
    dirs[-2:,:] = 1 # Border pixels flow outside the map
    dirs[:,-2:] = 2
    dirs[ :2,:] = 3
    dirs[:, :2] = 4

    lakes = np.zeros((Y, X))

    def add_point(y, x, altmax):
        alt = dem_margin[y, x]
        heapq.heappush(borders, (alt, altmax, y, x))

    while len(borders) > 0:
        (alt, altmax, y, x) = heapq.heappop(borders) # Take the lowest pixel in the queue
        neighbours = dirs[y-1:y+2, x-1:x+2]
        empty_neighbours = (neighbours == 0) * neighbours_pattern # Find the neighbours whose flow direction is not yet defined
        neighbours += empty_neighbours * neighbours_dirs # They flow into the pixel being studied

        lake = max(alt, altmax) # Set lake elevation to the maximal height of the downstream section.
        lakes[y-1,x-1] = lake

        coords = np.transpose(empty_neighbours.nonzero())
        for (dy,dx) in coords-1: # Add these neighbours into the queue
            add_point(y+dy, x+dx, lake)

    return dirs[1:-1,1:-1], lakes

def accumulate(dirs, dem=None):
    """
    Calculates the quantity of water that accumulates at every pixel,
    following flow directions.
    """

    (Y, X) = dirs.shape
    dirs_margin = np.zeros((Y+2,X+2))-1
    dirs_margin[1:-1,1:-1] = dirs
    quantity = np.zeros((Y, X), dtype='i4')

    def calculate_quantity(y, x):
        if quantity[y,x] > 0:
            return quantity[y,x]
        q = 1 # Consider that every pixel contains a water quantity of 1 by default.
        neighbours = dirs_margin[y:y+3, x:x+3]
        donors = neighbours == neighbours_dirs # Identify neighbours that give their water to the pixel being studied

        coords = np.transpose(donors.nonzero())
        for (dy,dx) in coords-1:
            q += calculate_quantity(y+dy, x+dx) # Add water quantity of the donors pixels (this triggers calculation for these pixels, recursively)
        quantity[y, x] = q
        return q

    for x in range(X):
        for y in range(Y):
            calculate_quantity(y, x)

    return quantity

def flow(dem):
    """
    Calculates flow directions and water quantity
    """

    dirs, lakes = flow_dirs_lakes(dem)
    return dirs, lakes, accumulate(dirs, dem)
