import numpy as np

def make_bounds(dirs, rivers):
    """
    Give an array of all horizontal and vertical bounds
    """

    (Y, X) = dirs.shape
    bounds_h = np.zeros((Y, X-1), dtype='i4')
    bounds_v = np.zeros((Y-1, X), dtype='i4')

    bounds_v += (rivers * (dirs==1))[:-1,:]
    bounds_h += (rivers * (dirs==2))[:,:-1]
    bounds_v -= (rivers * (dirs==3))[1:,:]
    bounds_h -= (rivers * (dirs==4))[:,1:]

    return bounds_h, bounds_v

def get_fixed(dirs):
    """
    Give the list of points that should not be twisted
    """

    borders = np.zeros(dirs.shape, dtype='?')
    borders[-1,:] |= dirs[-1,:]==1
    borders[:,-1] |= dirs[:,-1]==2
    borders[0,:] |= dirs[0,:]==3
    borders[:,0] |= dirs[:,0]==4

    donors = np.zeros(dirs.shape, dtype='?')
    donors[1:,:] |= dirs[:-1,:]==1
    donors[:,1:] |= dirs[:,:-1]==2
    donors[:-1,:] |= dirs[1:,:]==3
    donors[:,:-1] |= dirs[:,1:]==4
    return borders | ~donors

def twist(bounds_x, bounds_y, fixed, d=0.1, n=5):
    """
    Twist the grid (define an offset for every node). Model river bounds as if they were elastics.
    Smoothes preferentially big rivers.
    """

    moveable = ~fixed

    (Y, X) = fixed.shape
    offset_x = np.zeros((Y, X))
    offset_y = np.zeros((Y, X))

    for i in range(n):
        force_long = np.abs(bounds_x) * (1+np.diff(offset_x, axis=1))
        force_trans = np.abs(bounds_y) * np.diff(offset_x, axis=0)

        force_x = np.zeros((Y, X))
        force_x[:,:-1] = force_long
        force_x[:,1:] -= force_long
        force_x[:-1,:]+= force_trans
        force_x[1:,:] -= force_trans

        force_long = np.abs(bounds_y) * (1+np.diff(offset_y, axis=0))
        force_trans = np.abs(bounds_x) * np.diff(offset_y, axis=1)

        force_y = np.zeros((Y, X))
        force_y[:-1,:] = force_long
        force_y[1:,:] -= force_long
        force_y[:,:-1]+= force_trans
        force_y[:,1:] -= force_trans

        length = np.hypot(force_x, force_y)
        length[length==0] = 1
        coeff = d / length * moveable # Normalize, take into account the direction only
        offset_x += force_x * coeff
        offset_y += force_y * coeff

    return offset_x, offset_y
