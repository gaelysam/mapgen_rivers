local function distance_to_segment(x1, y1, x2, y2, x, y)
	-- get the distance between point (x,y) and segment (x1,y1)-(x2,y2)
	local a = (x1-x2)^2 + (y1-y2)^2 -- square of distance
	local b = (x1-x)^2 + (y1-y)^2
	local c = (x2-x)^2 + (y2-y)^2
	if a + b < c then
		-- The closest point of the segment is the extremity 1
		return math.sqrt(b)
	elseif a + c < b then
		-- The closest point of the segment is the extremity 2
		return math.sqrt(c)
	else
		-- The closest point is on the segment
		return math.abs(x1 * (y2-y) + x2 * (y-y1) + x * (y1-y2)) / math.sqrt(a)
	end
end

local function transform_quadri(X, Y, x, y)
	-- To index points in an irregular quadrilateral, giving x and y between 0 (one edge) and 1 (opposite edge)
	-- X, Y 4-vectors giving the coordinates of the 4 vertices
	-- x, y position to index.
	local x1, x2, x3, x4 = unpack(X)
	local y1, y2, y3, y4 = unpack(Y)

	-- Compare distance to 2 opposite edges, they give the X coordinate
	local d23 = distance_to_segment(x2,y2,x3,y3,x,y)
	local d41 = distance_to_segment(x4,y4,x1,y1,x,y)
	local xc = d41 / (d23+d41)

	-- Same for the 2 other edges, they give the Y coordinate
	local d12 = distance_to_segment(x1,y1,x2,y2,x,y)
	local d34 = distance_to_segment(x3,y3,x4,y4,x,y)
	local yc = d12 / (d12+d34)
	return xc, yc
end

return transform_quadri
