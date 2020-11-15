# Map Generator with Rivers
`mapgen_rivers v0.0` by Gaël de Sailly.

Procedural map generator for Minetest 5.x. It aims to create realistic and nice-looking landscapes for the game, focused on river networks. It is based on algorithms modelling water flow and river erosion at a broad scale, similar to some used by researchers in Earth Sciences. It is taking some inspiration from [Fastscape](https://github.com/fastscape-lem/fastscape).

Its main particularity compared to conventional Minetest mapgens is that rivers that flow strictly downhill, and combine together to form wider rivers, until they reach the sea. Another notable feature is the possibility of large lakes above sea level.

![Screenshot](https://user-images.githubusercontent.com/6905002/98825953-6289d980-2435-11eb-9e0b-704a95663ce0.png)

**Important to know**: Unlike most other Minetest mods, it does not contain standalone Lua code, but does part of its processing with a separate Python program (included).
- The Python part does pre-processing: it creates large-scale terrain data and applies landscape evolution algorithms, then outputs a grid of data in the mod's or world's folder. The grid is typically an array of 1000x1000 points of data, each of them representing a cell (by default 12x12 nodes). This pre-processing is long and should be run in advance.
- The Lua part does actual map generation on Minetest. It reads grid data, upscales it (by a factor 12 by default), and adds small-scale features.

# Requirements
Mod dependencies: `default` required, and [`biomegen`](https://github.com/Gael-de-Sailly/biomegen) optional.

Map pre-generation requires Python 3 with the following libraries installed:
- `numpy`, widely used library for numerical calculations
- `scipy`, a library for advanced data treatments, that is used here for Gaussian filtering
- `noise`, implementing Perlin/Simplex noises

Also, the following are optional (for map preview)
- `matplotlib`, a famous library for graphical plotting
- `colorcet` if you absolutely need better colormaps for preview :-)

They are all commonly found on `pip` or `conda` Python distributions.

# Installation
This mod should be placed in the `mods/` directory of Minetest like any other mod.

# Usage
By default, the mod contains a demo 400x400 grid (so you can start the game directly), but it is recommended to run the pre-processing script to generate a new grid before world creation, if you can.

1. Run the script `generate.py` to generate a grid, preferentially from inside the mod's directory, but you can also run it directly in a Minetest world. See next paragraph for details about parameters.
```
./generate.py
```
2. Start Minetest, create a world with `singlenode` mapgen, enable `mapgen_rivers` mod, and launch the game. If you generated a grid in the world directory, it will copy it. If not, it will use the demo grid.

## Parameters for `generate.py`
For a basic use you do not need to append any argument:
```
./generate.py
```
By default this will produce a 1000x1000 grid and save it in `river_data/`. Expect a computing time of about 30 minutes.

### Parameters and config files
This pre-processing takes many parameters. Instead of asking all these parameters to the end user, they are grouped in `.conf` files for usability, but the script still allows to override individual settings.

Generic usage:
```
./generate.py conf_file output_dir
```

- `conf_file`: Path to configuration file from which parameters should be read. If omitted, attempts to read in `terrain.conf`.
- `output_dir`: Directory in which to save the grid data, defaults to `river_data/`. If it does not exist, it is created. If it already contains previous grid data, they are overwritten.

### Complete list of parameters
Other parameters can be specified by `--parameter value`. Syntax `--parameter=value` is also supported.

| Parameter     | Description | Example |
|---------------|-------------|---------|
| | **Generic parameters** |
| `mapsize`     | Size of the grid, in number of cells per edge. Usually `1000`, so to have 1000x1000 cells, the grid will have 1001x1001 nodes. Note that the grid is upscaled 12x in the game (this ratio can be changed), so that a `mapsize` of 1000 will result in a 12000x12000 map by default. | `--mapsize 1000` |
| `sea_level`   | Height of the sea; height below which a point is considered under water even if it is not in a closed depression. | `--sea_level 1` |
| | **Noise parameters** |
| `scale`       | Horizontal variation wavlength of the largest noise octave, in grid cells (equivalent to the `spread` of a `PerlinNoise`). | `--scale 400` |
| `vscale`      | Elevation coefficient, determines the approximate height difference between deepest seas and highest mountains. | `--vscale 300` |
| `offset`      | Offset of the noise, will determine mean elevation. | `--offset 0` |
| `persistence` | Relative height of smaller noise octaves compared to bigger ones. | `--persistence 0.6` |
| `lacunarity`  | Relative reduction of wavelength between octaves. If `lacunarity`×`persistence` is larger than 1 (usual case), smaller octaves result in higher slopes than larger ones. This case is interesting for rivers networks because slopes determine rivers position. | `--lacunarity 2` |
| | **Landscape evolution parameters**|
| `K`           | Abstract erosion constant. Increasing it will increase erosive intensity. | `--K 1` |
| `m`           | Parameter representing the influence of river flux on erosion. For `m=0`, small and big rivers are equal contributors to erosion. For `m=1` the erosive capability is proportional to river flux (assumed to be catchment area). Usual values: `0.25`-`0.60`. Be careful, this parameter is *highly sensitive*. | `--m 0.35` |
| `d`           | Diffusion coefficient acting on sea/lake floor. Usual values `0`-`1`. | `--d 0.2` |
| `flex_radius` | Flexure radius. Wavelength over which loss/gain of mass is compensated by uplift/subsidence. This ensures that mountain ranges will not get eventually flattened by erosion, and that an equilibrium is reached. Geologically speaking, this implements [isostatic rebound](https://en.wikipedia.org/wiki/Isostasy). | `--flex_radius 20` |
| `time`        | Simulated time of erosion modelling, in abstract units. | `--time 10` |
| `niter`       | Number of iterations. Each iteration represents a time `time/niter`. | `--niter 10` |
| | **Alternatives** |
| `config`      | Another way to specify configuration file | `--config terrain_higher.conf` |
| `output`      | Another way to specify output dir | `--output ~/.minetest/worlds/my_world/river_data` |

### Example
```
./generate.py terrain_higher.conf --mapsize 700 --K 0.4 --m 0.5
```
Reads parameters in `terrain_higher.conf`, and will generate a 700x700 grid using custom values for `K` and `m`.

## Map preview
If you have `matplotlib` installed, `generate.py` will automatically show the grid aspect in real time during the erosion simulation.

There is also a script to view a generated map afterwards: `view_map.py`. Its syntax is the following:
```
./view_map.py grid blocksize
```

- `grid` is the path to the grid directory to view. For example `river_data/`.
- `blocksize` is the size at which 1 grid cell will be upscaled, in order to match game coordinates. If you use default settings, use `12`.

Example:
```
./view_map.py river_data 12
```
