#!/bin/bash
ls TopoUTM33/*.zip | parallel ./parseWater.sh

for z in TopoUTM33Tung/*.zip
do
	echo "Parsing $z"
	./parseWater.sh $z
done