'''
Created on Nov 29, 2014

@author: torsteinibo
'''

from lxml import etree
from nodes2nodeList import nodes2nodeList
import sys
from copy import deepcopy
from math import floor
from emptyRemover import emptyRemover

def openOsm(fileName):
    return etree.parse(fileName)

def keepNodesInWay(way,removeNodes,keptNodes):
    for nd in way.findall("nd"):
        if nd.attrib["ref"] in removeNodes:
            removeNodes.remove(nd.attrib["ref"])
            keptNodes.add(nd.attrib["ref"])
                
def keepNodesInWaySplitter(way,splitNodes):
    for nd in way.findall("nd"):
        if nd.attrib["ref"] not in splitNodes:
            splitNodes.add(nd.attrib["ref"])

def splitter(osmFile,latMin,latMax,lonMin,lonMax):
    
    splitFile = deepcopy(osmFile)
    nodes = nodes2nodeList(osmFile.xpath("node"))
    removeNodes = set()
    splitNodes = set()
    for ref,nd in nodes.iteritems():
        lat = float(nd.attrib["lat"])
        lon = float(nd.attrib["lon"])
        if (lat <= latMin or lat >= latMax or lon <= lonMin or lon >= lonMax):
            removeNodes.add(ref)
            splitNodes.add(ref)
    
    ways = nodes2nodeList(osmFile.xpath("way"))
    keptNodes = set() #Nodes kept which are outside of the bbox
    removeWays = set()
    splitWays = set()
    for ref,way in ways.iteritems():
        # Check if any are inside
        inside = False
        for nd in way.findall("nd"):
            if not ((nd.attrib["ref"] in removeNodes) or (nd.attrib["ref"] in keptNodes)):
                inside = True
                break
            
        if inside:
            keepNodesInWay(way,removeNodes,keptNodes)
        else:
            removeWays.add(ref)
            splitWays.add(ref)
            keepNodesInWaySplitter(way, splitNodes)
            
    keptWays = set()
    #ways kept to keep relation complete
    for rel in osmFile.xpath("relation"):
        inside = False
        for member in rel.findall("member"):
            if member.attrib["type"] == "way":
                if not ((member.attrib["ref"] in removeWays) or (member.attrib["ref"] in keptWays)):
                    inside = True
                    break
            elif member.attrib["type"] == "node":
                if not ((member.attrib["ref"] in removeNodes) or (member.attrib["ref"] in keptNodes)):
                    inside = True
                    break
        if inside:
            Sroot = splitFile.getroot()
            Sroot.remove(Sroot.find("relation[@id='%s']"%rel.attrib['id']))
            for member in rel.findall("member"):
                if member.attrib["type"] == "way" and (member.attrib["ref"] in removeWays):
                    removeWays.remove(member.attrib["ref"])
                    keptWays.add(member.attrib["ref"])
                    keepNodesInWay(ways[member.attrib["ref"]],removeNodes,keptNodes)
                elif member.attrib["type"] == "node" and (member.attrib["ref"] in removeNodes):
                    removeNodes.remove(member.attrib["ref"])
                    keptNodes.add(member.attrib["ref"])
        else:
            osmFile.getroot().remove(rel)
            for member in rel.findall("member"):
                if member.attrib["type"] == "way" and (member.attrib["ref"] not in splitWays):
                    splitWays.add(member.attrib["ref"])
                    keepNodesInWaySplitter(ways[member.attrib["ref"]],splitNodes)
                elif member.attrib["type"] == "node" and (member.attrib["ref"] in splitNodes):
                    splitNodes.add(member.attrib["ref"])

    for ref in removeNodes:
        osmFile.getroot().remove(nodes[ref])

    for ref in removeWays:
        osmFile.getroot().remove(ways[ref])
    
    if len(splitNodes) == len(nodes):
        return (None,splitFile)  
      
    for nd in splitFile.xpath("node"):
        if nd.attrib["id"] not in splitNodes:
            splitFile.getroot().remove(nd)
    
    for way in splitFile.xpath("way"):
        if way.attrib["id"] not in splitWays:
            splitFile.getroot().remove(way)

    return (osmFile,splitFile)

if __name__ == '__main__':
    fileName = None
    if (len(sys.argv) != 3):
        print("""The script requires two inputs:
Usage:
python replaceWithOsm.py inputFile outputFilePrefix
            
            """)
        exit()
    else:
        fileName = sys.argv[1]
        fileNameOut = sys.argv[2]

        osmFile = openOsm(fileName)
        latMin = 180
        latMax = -180
        lonMin = 180
        lonMax = -180
        for node in osmFile.xpath("node"):
            lat = float(node.attrib["lat"])
            lon = float(node.attrib["lon"])
            latMin = min(lat,latMin)
            lonMin = min(lon,lonMin)
            latMax = max(lat,latMax)
            lonMax = max(lon,lonMax)
        delta = .15
        latMin -= latMin % delta
        lonMin -= lonMin % delta
        for i in range(int((latMax-latMin)/delta+1)):
            lat = latMin+i*delta
            (band, osmFile) = splitter(osmFile, lat, lat+delta, -180, 180)
            for j in range(int((lonMax-lonMin)/delta+1)):
                lon = lonMin+j*delta
                (sub, band) = splitter(band, lat, lat+delta, lon, lon+delta)
                if sub is not None:
                    sub = emptyRemover(sub)
                    sub.write("%s_%.2f_%.2f.osm" % (fileNameOut,lat,lon))

