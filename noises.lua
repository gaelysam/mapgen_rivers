mapgen_rivers.noise_params = {
	distort_x = {
		offset = 0,
		scale = 1,
		seed = -4574,
		spread = {x=64, y=32, z=64},
		octaves = 3,
		persistence = 0.75,
		lacunarity = 2,
	},

	distort_z = {
		offset = 0,
		scale = 1,
		seed = -7940,
		spread = {x=64, y=32, z=64},
		octaves = 3,
		persistence = 0.75,
		lacunarity = 2,
	},

	distort_amplitude = {
		offset = 0,
		scale = 10,
		seed = 676,
		spread = {x=1024, y=1024, z=1024},
		octaves = 5,
		persistence = 0.5,
		lacunarity = 2,
		flags = "absvalue",
	},

	heat = minetest.get_mapgen_setting_noiseparams('mg_biome_np_heat'),
	heat_blend = minetest.get_mapgen_setting_noiseparams('mg_biome_np_heat_blend'),
}

mapgen_rivers.noise_params.heat.offset = mapgen_rivers.noise_params.heat.offset + mapgen_rivers.sea_level*mapgen_rivers.elevation_chill
