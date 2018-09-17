#!/bin/sh

#  parseAll.sh
#
#
#  Created by Torstein I. Bø on 02/04/2017.
#

if [ ! -d "tmp" ]; then
  mkdir "tmp"
fi
if [ ! -d "Converted" ]; then
  mkdir "Converted"
fi

./parseAllWater.sh
./parseAllArea.sh
./parseAllCoast.sh
