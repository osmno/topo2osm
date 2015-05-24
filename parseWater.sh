#!/bin/bash

file="$1"
id=$(echo $file | grep -o '[1-2]*\d\d\d')
name=$(echo $file | grep -o '[a-zæøåA-ZÆØÅ]*_UTM\d\d');
if [ ${#id} -lt 4 ]
  then 
    id="0$id";
fi

unzip -uq $file "${id}_N50_Arealdekke.sos"
sosi2osm "${id}_N50_Arealdekke.sos" vann.lua ${id}.osm
python riverTurner.py ${id}.osm ${id}.osm
python waySimplifyer.py ${id}.osm ${id}.osm
python emptyRemover.py ${id}.osm ${id}.osm
python removeExcessiveNodes.py ${id}.osm ${id}.osm .1
python splitterOsm.py ${id}.osm ${id}_part
zip -q "/Users/torsteinibo/Google Drive/TopoImportVann/${id}_${name}_vann.zip" ${id}*.osm
rm ${id}.osm
rm ${id}*.osm
rm "${id}_N50_Arealdekke.sos"