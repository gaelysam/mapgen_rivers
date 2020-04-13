local modpath = minetest.get_modpath(minetest.get_current_modname()) .. '/'
local worldpath = minetest.get_worldpath() .. '/'
local load_map = dofile(modpath .. 'load.lua')
local geometry = dofile(modpath .. 'geometry.lua')

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

copy_if_needed('offset_x')
local offset_x = load_map(worldpath..'offset_x', 1, true)
for k, v in ipairs(offset_x) do
	offset_x[k] = (v+0.5)/256
end

copy_if_needed('offset_y')
local offset_z = load_map(worldpath..'offset_y', 1, true)
for k, v in ipairs(offset_z) do
	offset_z[k] = (v+0.5)/256
end


local function index(x, z)
	return z*X+x+1
end

local function get_point_location(x, z)
	local i = index(x, z)
	return x+offset_x[i], z+offset_z[i]
end

local function interp(v00, v01, v10, v11, xf, zf)
	local v0 = v01*xf + v00*(1-xf)
	local v1 = v11*xf + v10*(1-xf)
	return v1*zf + v0*(1-zf)
end

local data = {}

local blocksize = 12
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
	local chulens = maxp.z - minp.z + 1

	local polygons = {}
	local xpmin, xpmax = math.max(math.floor(minp.x/blocksize - 0.5), 0), math.min(math.ceil(maxp.x/blocksize), X-2)
	local zpmin, zpmax = math.max(math.floor(minp.z/blocksize - 0.5), 0), math.min(math.ceil(maxp.z/blocksize), Z-2)

	for xp = xpmin, xpmax do
		for zp=zpmin, zpmax do
			local iA = index(xp, zp)
			local iB = index(xp+1, zp)
			local iC = index(xp+1, zp+1)
			local iD = index(xp, zp+1)
			local poly_x = {offset_x[iA]+xp, offset_x[iB]+xp+1, offset_x[iC]+xp+1, offset_x[iD]+xp}
			local poly_z = {offset_z[iA]+zp, offset_z[iB]+zp, offset_z[iC]+zp+1, offset_z[iD]+zp+1}
			local polygon = {x=poly_x, z=poly_z, i={iA, iB, iC, iD}}

			local bounds = {}
			local xmin = math.max(math.floor(blocksize*math.min(unpack(poly_x)))+1, minp.x)
			local xmax = math.min(math.floor(blocksize*math.max(unpack(poly_x))), maxp.x)
			for x=xmin, xmax do
				bounds[x] = {}
			end

			local i1 = 4
			for i2=1, 4 do -- Loop on 4 edges
				local x1, x2 = poly_x[i1], poly_x[i2]
				local lxmin = math.floor(blocksize*math.min(x1, x2))+1
				local lxmax = math.floor(blocksize*math.max(x1, x2))
				if lxmin <= lxmax then
					local z1, z2 = poly_z[i1], poly_z[i2]
					local a = (z1-z2) / (x1-x2)
					local b = blocksize*(z1 - a*x1)
					for x=math.max(lxmin, minp.x), math.min(lxmax, maxp.x) do
						table.insert(bounds[x], a*x+b)
					end
				end
				i1 = i2
			end
			for x=xmin, xmax do
				local xlist = bounds[x]
				table.sort(xlist)
				local c = math.floor(#xlist/2)
				for l=1, c do
					local zmin = math.max(math.floor(xlist[l*2-1])+1, minp.z)
					local zmax = math.min(math.floor(xlist[l*2]), maxp.z)
					local i = (x-minp.x) * chulens + (zmin-minp.z) + 1
					for z=zmin, zmax do
						polygons[i] = polygon
						i = i + 1
					end
				end
			end
		end
	end

	local i = 1
	for x = minp.x, maxp.x do
		for z = minp.z, maxp.z do
			local poly = polygons[i]
			if poly then
				local xf, zf = geometry.transform_quadri(poly.x, poly.z, x/blocksize, z/blocksize)
				if xf < 0 or xf > 1 or zf < 0 or zf > 1 then
					print(xf, zf, x, z)
				end
				local i00, i01, i11, i10 = unpack(poly.i)

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
				if xf < 1/6 then
					if links[i00] == 1 and rivers[i00] >= min_catchment then
						is_river = true
					elseif links[i10] == 3 and rivers[i10] >= min_catchment then
						is_river = true
					end
				end

				if zf < 1/6 then
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
			i = i + 1
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
