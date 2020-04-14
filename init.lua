mapgen_rivers = {}

local modpath = minetest.get_modpath(minetest.get_current_modname()) .. '/'

dofile(modpath .. 'settings.lua')

local blocksize = mapgen_rivers.blocksize
local sea_level = mapgen_rivers.sea_level
local riverbed_slope = mapgen_rivers.riverbed_slope

local make_polygons = dofile(modpath .. 'polygons.lua')

local transform_quadri = dofile(modpath .. 'geometry.lua')

local function interp(v00, v01, v11, v10, xf, zf)
	local v0 = v01*xf + v00*(1-xf)
	local v1 = v11*xf + v10*(1-xf)
	return v1*zf + v0*(1-zf)
end

local data = {}

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

	local polygons = make_polygons(minp, maxp)

	local i = 1
	for x = minp.x, maxp.x do
		for z = minp.z, maxp.z do
			local poly = polygons[i]
			if poly then
				local xf, zf = transform_quadri(poly.x, poly.z, x/blocksize, z/blocksize)
				local i00, i01, i11, i10 = unpack(poly.i)

				local is_river = false
				local depth_factor = 0
				local r_west, r_north, r_east, r_south = unpack(poly.rivers)
				if xf >= r_east then
					is_river = true
					depth_factor = xf-r_east
					xf = 1
				elseif xf <= r_west then
					is_river = true
					depth_factor = r_west-xf
					xf = 0
				end
				if zf >= r_south then
					is_river = true
					depth_factor = zf-r_south
					zf = 1
				elseif zf <= r_north then
					is_river = true
					depth_factor = r_north-zf
					zf = 0
				end

				if not is_river then
					local c_NW, c_NE, c_SE, c_SW = unpack(poly.river_corners)
					if xf+zf <= c_NW then
						is_river = true
						depth_factor = c_NW-xf-zf
						xf, zf = 0, 0
					elseif 1-xf+zf <= c_NE then
						is_river = true
						depth_factor = c_NE-1+xf-zf
						xf, zf = 1, 0
					elseif 2-xf-zf <= c_SE then
						is_river = true
						depth_factor = c_SE-2+xf+zf
						xf, zf = 1, 1
					elseif xf+1-zf <= c_SW then
						is_river = true
						depth_factor = c_SW-xf-1+zf
						xf, zf = 0, 1
					end
				end

				if not is_river then
					xf = (xf-r_west) / (r_east-r_west)
					zf = (zf-r_north) / (r_south-r_north)
				end

				local vdem = poly.dem
				local terrain_height = math.floor(0.5+interp(
					vdem[1],
					vdem[2],
					vdem[3],
					vdem[4],
					xf, zf
				))

				local lake_height = math.max(math.floor(poly.lake), terrain_height)
				if is_river then
					terrain_height = math.min(math.max(lake_height, sea_level) - math.floor(1+depth_factor*riverbed_slope), terrain_height)
				end
				local is_lake = lake_height > terrain_height
				local ivm = a:index(x, minp.y-1, z)
				if terrain_height >= minp.y then
					for y=minp.y, math.min(maxp.y, terrain_height) do
						if y == terrain_height then
							if is_lake or y <= sea_level then
								data[ivm] = c_sand
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
