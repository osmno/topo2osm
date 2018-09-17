#!/bin/bash

fileName="$1"
id=$(echo $fileName | grep -o '[0-9]\{3,4\}' | head -1)
kartverketPrefix=$(echo $fileName | grep -o 'Basisdata_.*_N50')
folder="tmp/${id}_water"
mkdir $folder
prefix="$folder/${id}_water"
if [ ${#id} -lt 4 ]
  then
    id="0$id";
fi
idName=$(echo $fileName | grep -o $id'\_[^_]\+');

set -e
set PYTHONPATH=/usr/local/lib/python2.7/dist-packages/osgeo

unzip -d $folder -uq $fileName "${kartverketPrefix}Arealdekke_SOSI.sos"
if $(file "$folder/${kartverketPrefix}Arealdekke_SOSI.sos" | grep -q 'UTF-8'); then
	iconv -c -tISO-8859-10 "$folder/${kartverketPrefix}Arealdekke_SOSI.sos" > "$folder/${id}_N50_ArealdekkeISO.sos"
	sed -i "s/UTF-8/ISO8859-10/" "$folder/${id}_N50_ArealdekkeISO.sos"
	mv "$folder/${id}_N50_ArealdekkeISO.sos" "$folder/${kartverketPrefix}Arealdekke_SOSI.sos"
fi
sosi2osm "$folder/${kartverketPrefix}Arealdekke_SOSI.sos" src/vann.lua > ${prefix}.osm
python src/riverTurner.py ${prefix}.osm ${prefix}.osm
python src/waySimplifyer.py ${prefix}.osm ${prefix}.osm
python src/emptyRemover.py ${prefix}.osm ${prefix}.osm
python src/removeExcessiveNodes.py ${prefix}.osm ${prefix}.osm .1
python src/splitterOsm.py ${prefix}.osm ${prefix}_part

rm "$folder/${kartverketPrefix}Arealdekke_SOSI.sos"
zip -rq "Converted/${idName}.zip" $folder/
rm $folder/*
rmdir $folder
