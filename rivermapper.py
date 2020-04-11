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

def flow_dirs_lakes(dem, random=0.0625):
    (Y, X) = dem.shape

    dem_margin = np.zeros((Y+2, X+2))
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

    heapq.heapify(borders)

    dirs = np.zeros((Y+2, X+2), dtype='u1')
    dirs[-2:,:] = 1
    dirs[:,-2:] = 2
    dirs[ :2,:] = 3
    dirs[:, :2] = 4

    lakes = np.zeros((Y, X))

    def add_point(y, x, altmax):
        alt = dem_margin[y, x]
        heapq.heappush(borders, (alt, altmax, y, x))

    while len(borders) > 0:
        (alt, altmax, y, x) = heapq.heappop(borders)
        neighbours = dirs[y-1:y+2, x-1:x+2]
        empty_neighbours = (neighbours == 0) * neighbours_pattern
        neighbours += empty_neighbours * neighbours_dirs

        lake = max(alt, altmax)
        lakes[y-1,x-1] = lake

        coords = np.transpose(empty_neighbours.nonzero())
        for (dy,dx) in coords-1:
            add_point(y+dy, x+dx, lake)

    return dirs[1:-1,1:-1], lakes

def accumulate(dirs, dem=None):
    (Y, X) = dirs.shape
    dirs_margin = np.zeros((Y+2,X+2))-1
    dirs_margin[1:-1,1:-1] = dirs
    quantity = np.zeros((Y, X), dtype='i4')

    def calculate_quantity(y, x):
        if quantity[y,x] > 0:
            return quantity[y,x]
        q = 1
        neighbours = dirs_margin[y:y+3, x:x+3]
        donors = neighbours == neighbours_dirs

        coords = np.transpose(donors.nonzero())
        for (dy,dx) in coords-1:
            q += calculate_quantity(y+dy, x+dx)
        quantity[y, x] = q
        return q

    for x in range(X):
        for y in range(Y):
            calculate_quantity(y, x)

    return quantity

def flow(dem):
    dirs, lakes = flow_dirs_lakes(dem)
    return dirs, lakes, accumulate(dirs, dem)
