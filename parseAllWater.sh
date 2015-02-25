#!/bin/bash
ls TopoUTM33/*.zip | parallel niceload -M 400M ./parseWater.sh

#for z in TopoUTM33/*.zip
#do
#	echo "Parsing $z"
#	./parseWater.sh $z
#done