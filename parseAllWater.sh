#!/bin/bash
#ls TopoUTM33/*.zip | parallel ./parseWater.sh

for z in N50/*.zip
do
	echo "Parsing $z"
	./parseWater.sh $z
done