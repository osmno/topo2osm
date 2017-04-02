#!/bin/bash
#ls TopoUTM33/*.zip | parallel ./parseArea.sh
for z in N50/*.zip
do
	echo "Parsing $z"
    date '+%A %W %Y %X'
	./parseArea.sh $z
done
