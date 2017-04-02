#!/bin/bash

fileName="$1"
id=$(echo $fileName | grep -o '[0-9]\{3,4\}' | head -1)
folder="tmp/${id}_coast"
mkdir $folder
prefix="$folder/${id}_coast"
name=$(echo $fileName | grep -o '[a-zæøåA-ZÆØÅ]*_UTM\d\d');
if [ ${#id} -lt 4 ]
  then 
    id="0$id";
fi

set -e


unzip -d $folder -uq $fileName "${id}_N50_Arealdekke.sos"
if $(file "$folder/${id}_N50_Arealdekke.sos" | grep -q 'UTF-8'); then
	iconv -c -tISO-8859-10 "$folder/${id}_N50_Arealdekke.sos" > "$folder/${id}_N50_ArealdekkeISO.sos"
	sed -i "s/UTF-8/ISO8859-10/" "$folder/${id}_N50_ArealdekkeISO.sos"
	mv "$folder/${id}_N50_ArealdekkeISO.sos" "$folder/${id}_N50_Arealdekke.sos"
fi
sosi2osm "$folder/${id}_N50_Arealdekke.sos" src/kyst.lua ${prefix}.osm
python src/waySimplifyer.py ${prefix}.osm ${prefix}.osm
python src/emptyRemover.py ${prefix}.osm ${prefix}.osm
python src/coastCorrector.py ${prefix}.osm ${prefix}.osm
python src/removeExcessiveNodes.py ${prefix}.osm ${prefix}.osm .1
python src/splitterOsm.py ${prefix}.osm ${prefix}_part --keepAdjacentWays
rm "$folder/${id}_N50_Arealdekke.sos"
zip -rq "../Converted/${id}_${name}.zip" $folder/
rm $folder/*
rmdir $folder
