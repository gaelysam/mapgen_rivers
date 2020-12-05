import numpy as np
import numpy.random as npr
from collections import defaultdict

# This file provide functions to construct the river tree from an elevation model.
# Based on a research paper:
#   | Cordonnier, G., Bovy, B., and Braun, J.:
#   | A versatile, linear complexity algorithm for flow routing in topographies with depressions,
#   | Earth Surf. Dynam., 7, 549–562, https://doi.org/10.5194/esurf-7-549-2019, 2019.
# Big thanks to them for releasing this paper under a free license ! :)

# The algorithm here makes use of most of the paper's concepts, including the Planar Boruvka algorithm.
# Only flow_local and accumulate_flow are custom algorithms.

def flow_local(plist):
    """
    Determines a flow direction based on denivellation for every neighbouring node.
    Denivellation must be positive for downward and zero for flat or upward:
    dz = max(zref-z, 0)
    """
    psum = sum(plist)
    if psum == 0:
        return 0
    r = npr.random() * psum
    for i, p in enumerate(plist):
        if r < p:
            return i+1
        r -= p

def flow(dem):

    # Flow locally
    dirs1 = np.zeros(dem.shape, dtype=int)
    dirs2 = np.zeros(dem.shape, dtype=int)
    (X, Y) = dem.shape
    Xmax, Ymax = X-1, Y-1
    singular = []
    for x in range(X):
        z0 = z1 = z2 = dem[x,0]
        for y in range(Y):
            z0 = z1
            z1 = z2
            if y < Ymax:
                z2 = dem[x, y+1]

            plist = [
                max(z1-dem[x+1,y],0) if x<Xmax else 0, # 1: x -> x+1
                max(z1-z2,0),                          # 2: y -> y+1
                max(z1-dem[x-1,y],0) if x>0    else 0, # 3: x -> x-1
                max(z1-z0,0),                          # 4: y -> y-1
            ]
            
            pdir = flow_local(plist)
            dirs2[x,y] = pdir
            if pdir == 0:
                singular.append((x,y))
            elif pdir == 1:
                dirs1[x+1,y] += 1
            elif pdir == 2:
                dirs1[x,y+1] += 2
            elif pdir == 3:
                dirs1[x-1,y] += 4
            elif pdir == 4:
                dirs1[x,y-1] += 8

    # Compute basins
    basin_id = np.zeros(dem.shape, dtype=int)
    stack = []

    for i, s in enumerate(singular):
        queue = [s]
        while queue:
            x, y = queue.pop()
            basin_id[x,y] = i
            d = int(dirs1[x,y])

            if d & 1:
                queue.append((x-1,y))
            if d & 2:
                queue.append((x,y-1))
            if d & 4:
                queue.append((x+1,y))
            if d & 8:
                queue.append((x,y+1))

    del dirs1

    # Link basins
    nsing = len(singular)
    links = {}
    def add_link(b0, b1, elev, bound):
        b = (min(b0,b1),max(b0,b1))
        if b not in links or links[b][0] > elev:
            links[b] = (elev, bound)

    for x in range(X):
        b0 = basin_id[x,0]
        add_link(-1, b0, dem[x,0], (True, x, 0))
        for y in range(1,Y):
            b1 = basin_id[x,y]
            if b0 != b1:
                add_link(b0, b1, max(dem[x,y-1],dem[x,y]), (True, x, y))
            b0 = b1
        add_link(-1, b1, dem[x,Ymax], (True, x, Y))
    for y in range(Y):
        b0 = basin_id[0,y]
        add_link(-1, b0, dem[0,y], (False, 0, y))
        for x in range(1,X):
            b1 = basin_id[x,y]
            if b0 != b1:
                add_link(b0, b1, max(dem[x-1,y],dem[x,y]), (False, x, y))
            b0 = b1
        add_link(-1, b1, dem[Xmax,y], (False, X, y))

    # Computing basin tree
    graph = planar_boruvka(links)

    basin_links = defaultdict(dict)
    for elev, b1, b2, bound in graph:
        basin_links[b1][b2] = basin_links[b2][b1] = (elev, bound)
    basins = np.zeros(nsing+1)
    stack = [(-1, float('-inf'))]

    # Applying basin flowing
    dir_reverse = (0, 3, 4, 1, 2)
    while stack:
        b1, elev1 = stack.pop()
        basins[b1] = elev1

        for b2, (elev2, bound) in basin_links[b1].items():
            stack.append((b2, max(elev1, elev2)))

            # Reverse flow direction in b2 (TODO)
            isY, x, y = bound
            backward = True # Whether water will escape the basin in +X/+Y direction
            if not (x < X and y < Y and basin_id[x,y] == b2):
                if isY:
                    y -= 1
                else:
                    x -= 1
                backward = False
            d = 2*backward + isY + 1
            while d > 0:
                d, dirs2[x,y] = dirs2[x,y], d
                if d == 1:
                    x += 1
                elif d == 2:
                    y += 1
                elif d == 3:
                    x -= 1
                elif d == 4:
                    y -= 1
                d = dir_reverse[d]

            del basin_links[b2][b1]
        del basin_links[b1]

    # Calculating water quantity
    dirs2[-1,:][dirs2[-1,:]==1] = 0
    dirs2[:,-1][dirs2[:,-1]==2] = 0
    dirs2[0,:][dirs2[0,:]==3] = 0
    dirs2[:,0][dirs2[:,0]==4] = 0

    waterq = accumulate_flow(dirs2)

    return dirs2, basins[basin_id], waterq

def accumulate_flow(dirs):
    ndonors = np.zeros(dirs.shape, dtype=int)
    ndonors[1:,:] += dirs[:-1,:] == 1
    ndonors[:,1:] += dirs[:,:-1] == 2
    ndonors[:-1,:] += dirs[1:,:] == 3
    ndonors[:,:-1] += dirs[:,1:] == 4
    waterq = np.ones(dirs.shape, dtype=int)

    (X, Y) = dirs.shape
    rangeX = range(X)
    rangeY = range(Y)
    for x in rangeX:
        for y in rangeY:
            if ndonors[x,y] > 0:
                continue
            xw, yw = x, y
            w = waterq[xw, yw]
            while 1:
                d = dirs[xw, yw]
                if d <= 0:
                    break
                elif d == 1:
                    xw += 1
                elif d == 2:
                    yw += 1
                elif d == 3:
                    xw -= 1
                elif d == 4:
                    yw -= 1

                w += waterq[xw, yw]
                waterq[xw, yw] = w

                if ndonors[xw, yw] > 1:
                    ndonors[xw, yw] -= 1
                    break

    return waterq

def planar_boruvka(links):
    # Compute basin tree

    basin_list = defaultdict(dict)

    for (b1, b2), (elev, bound) in links.items():
        basin_list[b1][b2] = basin_list[b2][b1] = (elev, b1, b2, bound)

    threshold = 8
    lowlevel = {}
    for k, v in basin_list.items():
        if len(v) <= threshold:
            lowlevel[k] = v

    basin_graph = []
    n = len(basin_list)
    while n > 1:
        (b1, lnk1) = lowlevel.popitem()
        b2 = min(lnk1, key=lnk1.get)
        lnk2 = basin_list[b2]

        # Add link to the graph
        basin_graph.append(lnk1[b2])

        # Union : merge basin 1 into basin 2
        # First, delete the direct link
        del lnk1[b2]
        del lnk2[b1]

        # Look for basin 1's neighbours, and add them to basin 2 if they have a lower pass
        for k, v in lnk1.items():
            bk = basin_list[k]
            if k in lnk2 and lnk2[k] < v:
                del bk[b1]
            else:
                lnk2[k] = v
                bk[b2] = bk.pop(b1)

            if k not in lowlevel and len(bk) <= threshold:
                lowlevel[k] = bk

        if b2 in lowlevel:
            if len(lnk2) > threshold:
                del lowlevel[b2]
        elif len(lnk2) <= threshold:
            lowlevel[b2] = lnk2
        del lnk1

        n -= 1

    return basin_graph
