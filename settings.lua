local storage = minetest.get_mod_storage()
local settings = minetest.settings

local function get_settings(key, dtype, default)
	if storage:contains(key) then
		if dtype == "string" then
			return storage:get_string(key)
		elseif dtype == "int" then
			return storage:get_int(key)
		elseif dtype == "float" then
			return storage:get_float(key)
		end
	end

	local conf_val = settings:get('mapgen_rivers_' .. key)
	if conf_val then
		if dtype == "int" then
			conf_val = tonumber(conf_val)
			storage:set_int(key, conf_val)
		elseif dtype == "float" then
			conf_val = tonumber(conf_val)
			storage:set_float(key, conf_val)
		elseif dtype == "string" then
			storage:set_string(key, conf_val)
		end

		return conf_val
	else
		if dtype == "int" then
			storage:set_int(key, default)
		elseif dtype == "float" then
			storage:set_float(key, default)
		elseif dtype == "string" then
			storage:set_string(key, default)
		end

		return default
	end
end

return get_settings
