'''
Created on Nov 29, 2014

@author: torsteinibo
'''

from lxml import etree
from mergeroads import nodes2nodeList
import sys

def openOsm(fileName):
    return etree.parse(fileName)

def keepNodesInWay(way,removeNodes,keptNodes):
    for nd in way.findall("nd"):
        if nd.attrib["ref"] in removeNodes:
            removeNodes.remove(nd.attrib["ref"])
            keptNodes.add(nd.attrib["ref"])

def splitter(fileName,fileNameOut,latMin,latMax,lonMin,lonMax):
    osmFile = openOsm(fileName)
    nodes = nodes2nodeList(osmFile.xpath("node"))
    removeNodes = set()
    for ref,nd in nodes.iteritems():
        lat = float(nd.attrib["lat"])
        lon = float(nd.attrib["lon"])
        if (lat <= latMin or lat >= latMax or lon <= lonMin or lon >= lonMax):
            removeNodes.add(ref)
    
    ways = nodes2nodeList(osmFile.xpath("way"))
    keptNodes = set() #Nodes kept which are outside of the bbox
    removeWays = set()
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

    for ref in removeNodes:
        osmFile.getroot().remove(nodes[ref])

    for ref in removeWays:
        osmFile.getroot().remove(ways[ref])
    
    
    osmFile.write(fileNameOut)

if __name__ == '__main__':
    fileName = None
    if (len(sys.argv) != 7):
        print("""The script requires two inputs:
Usage:
python replaceWithOsm.py inputFile outPutfile latMin latMax lonMin lonMax
            
            """)
        exit()
    else:
        fileName = sys.argv[1]
        fileNameOut = sys.argv[2]
        latMin = float(sys.argv[3])
        latMax = float(sys.argv[4])
        if latMin > latMax:
            print("latMin is larger then latMax")
            exit()
        lonMin = float(sys.argv[5])
        lonMax = float(sys.argv[6])
        if lonMin > lonMax:
            print("lonMin is larger than lonMax")
        splitter(fileName, fileNameOut, latMin, latMax, lonMin, lonMax)
