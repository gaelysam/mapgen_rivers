local modpath = minetest.get_modpath(minetest.get_current_modname()) .. '/'
local worldpath = minetest.get_worldpath() .. '/'
local load_map = dofile(modpath .. 'load.lua')

local function copy_if_needed(filename)
	local wfilename = worldpath..filename
	local wfile = io.open(wfilename, 'r')
	if wfile then
		wfile:close()
		return
	end
	local mfilename = modpath..filename
	local mfile = io.open(mfilename, 'r')
	local wfile = io.open(wfilename, 'w')
	wfile:write(mfile:read("*all"))
	mfile:close()
	wfile:close()
end

copy_if_needed('size')
local sfile = io.open(worldpath..'size')
local X = tonumber(sfile:read('*l'))
local Z = tonumber(sfile:read('*l'))

copy_if_needed('dem')
local dem = load_map(worldpath..'dem', 2, true)
copy_if_needed('lakes')
local lakes = load_map(worldpath..'lakes', 2, true)
copy_if_needed('links')
local links = load_map(worldpath..'links', 1, false)
copy_if_needed('rivers')
local rivers = load_map(worldpath..'rivers', 4, false)

local function index(x, z)
	return z*X+x+1
end

local function interp(v00, v01, v10, v11, xf, zf)
	v0 = v01*xf + v00*(1-xf)
	v1 = v11*xf + v10*(1-xf)
	return v1*zf + v0*(1-zf)
end

local data = {}

local blocksize = 6
local sea_level = 1
local min_catchment = 25

local storage = minetest.get_mod_storage()
if storage:contains("blocksize") then
	blocksize = storage:get_int("blocksize")
else
	storage:set_int("blocksize", blocksize)
end
if storage:contains("sea_level") then
	sea_level = storage:get_int("sea_level")
else
	storage:set_int("sea_level", sea_level)
end
if storage:contains("min_catchment") then
	min_catchment = storage:get_float("min_catchment")
else
	storage:set_float("min_catchment", min_catchment)
end

local function generate(minp, maxp, seed)
	local c_stone = minetest.get_content_id("default:stone")
	local c_dirt = minetest.get_content_id("default:dirt")
	local c_lawn = minetest.get_content_id("default:dirt_with_grass")
	local c_sand = minetest.get_content_id("default:sand")
	local c_water = minetest.get_content_id("default:water_source")
	local c_rwater = minetest.get_content_id("default:river_water_source")

	local vm, emin, emax = minetest.get_mapgen_object("voxelmanip")
	vm:get_data(data)

	local a = VoxelArea:new({MinEdge = emin, MaxEdge = emax})
	local ystride = a.ystride -- Tip : the ystride of a VoxelArea is the number to add to the array index to get the index of the position above. It's faster because it avoids to completely recalculate the index.

	for x = minp.x, maxp.x do
		for z = minp.z, maxp.z do
			local xb = x/blocksize
			local zb = z/blocksize

			if xb >= 0 and xb < X-1 and zb >= 0 and zb < Z-1 then
				local x0 = math.floor(xb)
				local x1 = x0+1
				local z0 = math.floor(zb)
				local z1 = z0+1

				local xf = xb - x0
				local zf = zb - z0

				local i00 = index(x0,z0)
				local i01 = index(x1,z0)
				local i10 = index(x0,z1)
				local i11 = index(x1,z1)

				local terrain_height = math.floor(interp(
					dem[i00],
					dem[i01],
					dem[i10],
					dem[i11],
					xf, zf
				))

				local lake_height = math.floor(math.min(
					lakes[i00],
					lakes[i01],
					lakes[i10],
					lakes[i11]
				))

				local is_lake = lake_height > terrain_height

				local is_river = false
				if xf == 0 then
					if links[i00] == 1 and rivers[i00] >= min_catchment then
						is_river = true
					elseif links[i10] == 3 and rivers[i10] >= min_catchment then
						is_river = true
					end
				end

				if zf == 0 then
					if links[i00] == 2 and rivers[i00] >= min_catchment then
						is_river = true
					elseif links[i01] == 4 and rivers[i01] >= min_catchment then
						is_river = true
					end
				end
				
				local ivm = a:index(x, minp.y-1, z)

				if terrain_height >= minp.y then
					for y=minp.y, math.min(maxp.y, terrain_height) do
						if y == terrain_height then
							if is_lake or y <= sea_level then
								data[ivm] = c_sand
							elseif is_river then
								data[ivm] = c_rwater
							else
								data[ivm] = c_lawn
							end
						else
							data[ivm] = c_stone
						end
						ivm = ivm + ystride
					end
				end

				if lake_height > sea_level then
					if is_lake and lake_height > minp.y then
						for y=math.max(minp.y, terrain_height+1), math.min(maxp.y, lake_height) do
							data[ivm] = c_rwater
							ivm = ivm + ystride
						end
					end
				else
					for y=math.max(minp.y, terrain_height+1), math.min(maxp.y, sea_level) do
						data[ivm] = c_water
						ivm = ivm + ystride
					end
				end
			end
		end
	end

	vm:set_data(data)
	minetest.generate_ores(vm, minp, maxp)
	vm:set_lighting({day = 0, night = 0})
	vm:calc_lighting()
	vm:update_liquids()
	vm:write_to_map()
end

minetest.register_on_generated(generate)
