'''
Created on Nov 29, 2014

@author: torsteinibo
'''

from lxml import etree
from mergeroads import nodes2nodeList
from elevation import Elevation
import sys
import utm

elevation = Elevation()

def getElevation(node):
    lat = float(node.attrib['lat'])
    lon = float(node.attrib['lon'])    
    res =  utm.from_latlon(lat, lon, 33)
    return elevation.getElevation(res[0],res[1])

def turnTivers(fileName,fileNameOut):
    osmFile = etree.parse(fileName)
    
    ways = osmFile.xpath("way")
    nodes = nodes2nodeList(osmFile.findall("node"))
    for way in ways:
        for tag in way.findall("tag"):
            if "k" in tag.attrib and tag.attrib["k"] == "waterway" and (tag.attrib["v"] == "river" or tag.attrib["v"] == "stream"):
                nd = way.findall("nd")
                h1 = getElevation(nodes[nd[0].attrib['ref']])
                h2 = getElevation(nodes[nd[-1].attrib['ref']])
                if (h1 < h2):
                    for n in nd:
                        way.remove(n)
                        for i in range(len(nd)-1,-1,-1):
                            way.append(nd[i])
    
    osmFile.write(fileNameOut)


if __name__ == '__main__':
    fileName = "OppdalAraldekke.osm"
    if (len(sys.argv) != 3):
        print("""The script requires two inputs:
Usage:
python riverTurner.py inputFile outPutfile
            
            """)
        exit()
    fileName = sys.argv[1]
    fileNameOut = sys.argv[2]
    turnTivers(fileName, fileNameOut)
