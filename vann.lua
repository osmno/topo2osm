out = {}

for i, indent, tokens in tokens, info, 0 do
    if tokens[1] == "FLATE" then
		out["type"] = "multipolygon"
    elseif tokens[1] == "OBJTYPE" then
		if tokens[2] == "Innsjø" then
			out["natural"]="water"
        elseif tokens[2] == "ElvBekk" then
			out["waterway"]="river"
        elseif tokens[2] == "Dam" then
            out["waterway"]="dam"
        elseif tokens[2] == "Havflate" then
            return {}
        elseif tokens[2] == "HavElvSperre" then
            return {}
        elseif tokens[2] == "Kystkontur" then
            return {}
        else

		end
    elseif tokens[1] == "HØYDE" then
        out["ele"] = tokens[2]
    elseif tokens[1] == "VANNBR" then
        out["width"] = tokens[2]
    elseif tokens[1] == "DATAFANGSTDATO" then
        v = tokens[2]
        out["source:date"] = string.format("%s-%s-%s",string.sub(v,1,4),string.sub(v,5,6),string.sub(v,7,8))
        out["source"] = "Kartverket N50"
    elseif tokens[1] == "OPPDATERINGSDATO" then
    elseif tokens[1] == "KVALITET" then
    
    elseif tokens[1] == "KURVE" or tokens[1] == "PUNKT" or  tokens[1] == "VATNLNR" then
        
    elseif tokens[1] == "NAVN" then
        out["name"] = tokens[2]
    elseif #tokens == 2 then
        out[tokens[1]] = tokens[2]
    elseif #tokens > 2 then
        out["lko"..tokens[1]] = table.concat(tokens, "; ", 2)
    end
end

if out["waterway"] == "river" and (out["width"] == "1" or out["width"] == "2") then
    out["waterway"] = "stream"
end

if out["width"] == nil then
else
    if out["width"] == "4" or out["width"] == "5" then
        out["waterway"]=nil
        out["natural"]="water"
	out["water"] = "river"
        out["FIXME"]="Add waterway in middle of way to indicate direction of river and connect side rivers/streams to it."
    end
    out["width"] = nil
end


return out

