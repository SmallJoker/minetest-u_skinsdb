u_skins.file = minetest.get_worldpath() .. "/u_skins.mt"

u_skins.load = function()
	local file = io.open(u_skins.file, "r")
	if file then
		for line in file:lines() do
			local data = string.split(line, ' ', 2)
			u_skins.u_skins[data[1]] = data[2]
		end
		io.close(file)
	end
end
u_skins.load()

local ttime = 0
minetest.register_globalstep(function(t)
	ttime = ttime + t
	if ttime < 360 then --every 6min'
		return
	end
	if(u_skins.file_save) then
		u_skins.file_save = false
		u_skins.save()
	end
	ttime = 0
end)

minetest.register_on_shutdown(function()
	if(u_skins.file_save) then
		u_skins.save()
	end
end)

u_skins.save = function()
	local output = io.open(u_skins.file,'w')
	for name, skin in pairs(u_skins.u_skins) do
		if name and skin then
			if skin ~= "character_1" then
				output:write(name .. " " .. skin .. "\n")
			end
		end
	end
	io.close(output)
end

