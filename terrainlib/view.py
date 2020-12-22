#!/usr/bin/env python3

import numpy as np
import sys, traceback

has_matplotlib = True
try:
    import matplotlib.colors as mcl
    import matplotlib.pyplot as plt
    try:
        import colorcet as cc
        cmap1 = cc.cm.CET_L11
        cmap2 = cc.cm.CET_L12
    except ImportError: # No module colorcet
        import matplotlib.cm as cm
        cmap1 = cm.summer
        cmap2 = cm.Blues
except ImportError: # No module matplotlib
    has_matplotlib = False

if has_matplotlib:
    def view_map(dem, lakes, scale=1, sea_level=0.0, title=None):
        lakes_sea = np.maximum(lakes, sea_level)
        water = np.maximum(lakes_sea - dem, 0)
        max_elev = dem.max()
        max_depth = water.max()

        ls = mcl.LightSource(azdeg=315, altdeg=45)
        norm_ground = plt.Normalize(vmin=sea_level, vmax=max_elev)
        norm_sea = plt.Normalize(vmin=0, vmax=max_depth)
        rgb = ls.shade(dem, cmap=cmap1, vert_exag=1/scale, blend_mode='soft', norm=norm_ground)

        (X, Y) = dem.shape
        extent = (0, Y*scale, 0, X*scale)
        plt.imshow(np.flipud(rgb), extent=extent, interpolation='antialiased')
        alpha = (water > 0).astype('u1')
        plt.imshow(np.flipud(water), alpha=np.flipud(alpha), cmap=cmap2, extent=extent, vmin=0, vmax=max_depth, interpolation='antialiased')

        sm1 = plt.cm.ScalarMappable(cmap=cmap1, norm=norm_ground)
        plt.colorbar(sm1).set_label('Elevation')

        sm2 = plt.cm.ScalarMappable(cmap=cmap2, norm=norm_sea)
        plt.colorbar(sm2).set_label('Water depth')

        plt.xlabel('X')
        plt.ylabel('Z')

        if title is not None:
            plt.title(title, fontweight='bold')

    def update(*args, t=0.01, **kwargs):
        try:
            plt.clf()
            view_map(*args, **kwargs)
            plt.pause(t)
        except:
            traceback.print_exception(*sys.exc_info())

    def plot(*args, **kwargs):
        try:
            plt.clf()
            view_map(*args, **kwargs)
            plt.pause(0.01)
            plt.show()
        except Exception as e:
            traceback.print_exception(*sys.exc_info())

else:
    def update(*args, **kwargs):
        pass
    def plot(*args, **kwargs):
        pass

def stats(dem, lakes, scale=1):
    surface = dem.size

    continent = np.maximum(dem, lakes) >= 0
    continent_surface = continent.sum()

    lake = continent & (lakes>dem)
    lake_surface = lake.sum()

    print('---   General    ---')
    print('Grid size:    {:5d}x{:5d}'.format(dem.shape[0], dem.shape[1]))
    if scale > 1:
        print('Map size:     {:5d}x{:5d}'.format(int(dem.shape[0]*scale), int(dem.shape[1]*scale)))
    print()
    print('---   Surfaces   ---')
    print('Continents:        {:6.2%}'.format(continent_surface/surface))
    print('-> Ground:         {:6.2%}'.format((continent_surface-lake_surface)/surface))
    print('-> Lakes:          {:6.2%}'.format(lake_surface/surface))
    print('Oceans:            {:6.2%}'.format(1-continent_surface/surface))
    print()
    print('---  Elevations  ---')
    print('Mean elevation:      {:4.0f}'.format(dem.mean()))
    print('Mean ocean depth:    {:4.0f}'.format((dem*~continent).sum()/(surface-continent_surface)))
    print('Mean continent elev: {:4.0f}'.format((dem*continent).sum()/continent_surface))
    print('Lowest elevation:    {:4.0f}'.format(dem.min()))
    print('Highest elevation:   {:4.0f}'.format(dem.max()))
