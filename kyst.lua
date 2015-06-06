out = {}

for i, indent, tokens in tokens, info, 0 do
    if tokens[1] == "FLATE" then
		out["type"] = "multipolygon"
    elseif tokens[1] == "OBJTYPE" then
        if tokens[2] == "HavElvSperre" then
            out["natural"] = "coastline"
        elseif tokens[2] == "Kystkontur" then
            out["natural"] = "coastline"
        elseif tokens[2] == "Skjær" then
            out["seamark:type"] = "rock"
        else
            return {}
		end
    elseif tokens[1] == "HØYDE" then
        out["ele"] = tokens[2]
    elseif tokens[1] == "DATAFANGSTDATO" then
        v = tokens[2]
        out["source:date"] = string.format("%s-%s-%s",string.sub(v,1,4),string.sub(v,5,6),string.sub(v,7,8))
        out["source"] = "Kartverket N50"
    elseif tokens[1] == "NAVN" then
        out["name"] = tokens[2]
    end
end

return out

