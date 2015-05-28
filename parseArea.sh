#!/bin/bash

file="$1"
id=$(echo $file | grep -o '[0-9]\{3,4\}')
name=$(echo $file | grep -o '[a-zæøåA-ZÆØÅ]*_UTM33');
if [ ${#id} -lt 4 ]
  then 
    id="0$id";
fi

unzip -uq $file "${id}_N50_Arealdekke.sos"
sosi2osm "${id}_N50_Arealdekke.sos" arealdekkeUvann.lua ${id}.osm
python waySimplifyer.py ${id}.osm ${id}.osm
python emptyRemover.py ${id}.osm ${id}.osm
python removeExcessiveNodes.py ${id}.osm ${id}.osm .1
python simplifyRelations.py  ${id}.osm ${id}.osm
python splitterOsm.py ${id}.osm ${id}_part
zip -q "/home/torstein/Google Drive/TopoImport/${id}_${name}.zip" ${id}*.osm
rm ${id}.osm
rm ${id}*.osm
rm "${id}_N50_Arealdekke.sos"
