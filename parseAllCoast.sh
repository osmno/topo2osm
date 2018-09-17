#!/bin/bash
#ls TopoPri/*.zip | parallel ./parseCoast.sh

for z in N50/*.zip
do
	echo "Parsing $z (coast)"
	./parseCoast.sh $z
done
