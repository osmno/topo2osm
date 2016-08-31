#!/bin/bash

file="$1"
id=$(echo $file | grep -o '[0-9]\{3,4\}')
folder="${id}_water"
mkdir $folder
prefix="$folder/${id}_water"
name=$(echo $file | grep -o '[a-zæøåA-ZÆØÅ]*_UTM33');
if [ ${#id} -lt 4 ]
  then 
    id="0$id";
fi

set -e
set PYTHONPATH=/usr/local/lib/python2.7/dist-packages/osgeo

unzip -uq $file "${id}_N50_Arealdekke.sos"
sosi2osm "${id}_N50_Arealdekke.sos" vann.lua ${prefix}.osm
python riverTurner.py ${prefix}.osm ${prefix}.osm
python waySimplifyer.py ${prefix}.osm ${prefix}.osm
python emptyRemover.py ${prefix}.osm ${prefix}.osm
python removeExcessiveNodes.py ${prefix}.osm ${prefix}.osm .1
python splitterOsm.py ${prefix}.osm ${prefix}_part
zip -rq "../../Google Drive/TopoImport/${id}_${name}.zip" $folder/
#zip -rq "/Users/torsteinibo/Google Drive/TopoImport/${id}_${name}.zip" $folder/
rm $folder/*
rmdir $folder
rm "${id}_N50_Arealdekke.sos"
