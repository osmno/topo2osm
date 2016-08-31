#!/bin/bash
ls TopoPri/*.zip | parallel ./parseCoast.sh

for z in TopoPriTung/*.zip
do
	echo "Parsing $z"
	./parseCoast.sh $z
done