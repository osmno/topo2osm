out = {}

for i, indent, tokens in tokens, info, 0 do
    if tokens[1] == "FLATE" then
		out["type"] = "multipolygon"
    elseif tokens[1] == "OBJTYPE" then
		if tokens[2] == "Myr" then
			out["natural"]="wetland"
			out["wetland"]="bog"
        elseif tokens[2] == "SnøIsbre" then
            out["natural"]="glacier"
        elseif tokens[2] == "FerskvannTørrfall" then
            out["natural"]="shingle"
            out["intermittent"]="yes"
            out["waterway"]="riverbank"
            out["FIXME"]="Check whether the surface should be natural=shingle or natural=sand"
        elseif tokens[2] == "Skog" then
            out["natural"]="wood"
        elseif tokens[2] == "DyrketMark" then
            out["landuse"]="farmland"
        elseif tokens[2] == "ÅpentOmråde" then

        elseif tokens[2] == "Tettbebyggelse" then
            out["landuse"]="residential"
        elseif tokens[2] == "Industriområde" then
            out["landuse"]="industrial"
        elseif tokens[2] == "BymessigBebyggelse" then
            out["landuse"]="residential"
	elseif tokens[2] == "Hyttefelt" then
            out["landuse"]="residential"
	    out["residential"]="cabin"
        elseif tokens[2] == "Havflate" then
            return {}
        elseif tokens[2] == "SportIdrettPlass" then
            out["leisure"] = "pitch"
	elseif tokens[2] == "Skytefelt" then
            out["leisure"] = "pitch"
	    out["sport"] = "shooting"
        elseif tokens[2] == "Park" then
            out["leisure"] = "park"
        elseif tokens[2] == "Gravplass" then
            out["landuse"] = "cemetery"
        elseif tokens[2] == "Golfbane" then
            out["leisure"] = "golf_course"
        elseif tokens[2] == "Steinbrudd" then
            out["landuse"] = "quarry"
        elseif tokens[2] == "Alpinbakke" then
            out["route"] = "piste"
            out["piste:type"] = "downhill"
        elseif tokens[2] == "Rullebane" then
            out["aeroway"] = "runway"
            out["FIXME"] = "Draw runway and taxiway as ways, and apron as area/polygon. If this is a taxiway or apron, use aeroway=taxiway or aeroway=apron instead."
        elseif tokens[2] == "Taksebane" then
            out["aeroway"] = "taxiway"
            out["FIXME"] = "Draw taxiway and runway as ways, and apron as area/polygon. If this is a runway or apron, use aeroway=runway or aeroway=apron instead."
        elseif tokens[2] == "Arealbrukgrense" then
        
        elseif tokens[2] == "FiktivDelelinje" then
        
        elseif tokens[2] == "Innsjøkant" then
        
        elseif tokens[2] == "KantUtsnitt" then

        elseif tokens[2] == "InnsjøkantRegulert" then
        
        elseif tokens[2] == "ElvBekkKant" then

        elseif tokens[2] == "Helikopterplass" then
            out["aeroway"] = "helipad"
        elseif tokens[2] == "Skjær" then
            out["seamark:type"] = "rock"
        elseif tokens[2] == "Tregruppe" then
            out["natural"] = "tree"
        elseif tokens[2] == "Dataavgrensning" then

		end
    elseif tokens[1] == "HØYDE" then
        out["ele"] = tokens[2]
    elseif tokens[1] == "DATAFANGSTDATO" then
        v = tokens[2]
        out["source:date"] = string.format("%s-%s-%s",string.sub(v,1,4),string.sub(v,5,6),string.sub(v,7,8))
        out["source"] = "Kartverket N50"
    elseif tokens[1] == "OPPDATERINGSDATO" then
    elseif tokens[1] == "KVALITET" then
    
    elseif tokens[1] == "KURVE" or tokens[1] == "PUNKT" or  tokens[1] == "VATNLNR" then
        
    elseif tokens[1] == "NAVN" then
        out["name"] = tokens[2]
    elseif #tokens > 2 then
        out["lko"..tokens[1]] = table.concat(tokens, "; ", 2)
    end
end

return out

