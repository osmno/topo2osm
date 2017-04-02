#!/bin/bash
#ls TopoPri/*.zip | parallel ./parseCoast.sh

for z in N50/*.zip
do
	echo "Parsing $z"
	./parseCoast.sh $z
done