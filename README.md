mapgen_rivers
=============

Procedural map generator for Minetest 5.x. Focused on river networks, and features valley erosion and lakes.

Contains two distinct programs: Python scripts for pre-processing, and Lua scripts to generate the map on Minetest.

![Screenshot](https://user-images.githubusercontent.com/6905002/79541028-687b3000-8089-11ea-9209-c23c15d75383.png)

# Installation
This mod should be placed in the `/mods` directory like any other Minetest mod.

The Python part relies on external libraries that you need to install:
- `numpy` and `scipy`, widely used libraries for numerical calculations
- `noise`, doing Perlin/Simplex noises
- optionally, `matplotlib` (for map preview)

They are commonly found on `pip` or `conda` Python distributions.

# Usage
By default, the mod contains a demo 400x400 map (so you can start the game directly), but it is recommended that you run the pre-processing script to generate a new map before world creation, if you can.

## Pre-processing
Run the script `terrain_rivers.py` via command line. You can optionally append the map size (by default 400). Example for a 1000x1000 map:
```
./terrain_rivers.py 1000
```
For a default 400x400 map, it should take between 1 and 2 minutes. It will generate 5 files directly in the mod folder, containing the map data.

If you have `matplotlib` installed, the script `view_map.py` can be used to get a map preview. Example:
```
./view_map.py data/
```

## Map generation
Just create a Minetest world with `singlenode` mapgen, enable this mod and start the world. The data files are immediately copied in the world folder so you can re-generate them afterwards, it won't affect the old worlds.
