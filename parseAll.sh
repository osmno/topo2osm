#!/bin/sh

#  parseAll.sh
#
#
#  Created by Torstein I. Bø on 02/04/2017.
#

if [ ! -d "tmp" ]; then
  mkdir "tmp"
fi

./parseAllWater.sh
./parseAllArea.sh
./parseAllCoast.sh
