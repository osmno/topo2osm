#!/bin/bash
ls TopoUTM33/*.zip | parallel ./parseCoast.sh

for z in TopoUTM33Tung/*.zip
do
	echo "Parsing $z"
	./parseCoast.sh $z
done