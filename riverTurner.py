'''
Created on Nov 29, 2014

@author: torsteinibo
'''

from lxml import etree
from mergeroads import nodes2nodeList
from elevation import Elevation
import sys
import utm
from math import fabs
import os

elevation = Elevation()

def getElevation(node):
    lat = float(node.attrib['lat'])
    lon = float(node.attrib['lon'])    
    res =  utm.from_latlon(lat, lon, 33)
    return elevation.getElevation(res[0],res[1])

def reverseWay(way,nd=None):
    if nd is None:
        nd = way.findall("nd")
    for n in nd:
        way.remove(n)
    for i in range(len(nd)-1,-1,-1):
        way.append(nd[i])
        
class NodeStatus:
    def __init__(self):
        self.lowNodes = set()
        self.heighNodes = set()
        self.unknownNodes = set()
        
    def addLowNode(self,ref):
        self.lowNodes.add(ref)
        
    def addHeighNode(self,ref):
        self.heighNodes.add(ref)
        
    def addUnknownNode(self,ref):
        self.unknownNodes.add(ref)
    
    # Returns 1 if ref is the heighest (inlet)
    # Returns 0 if unknown
    # Returns -1 if ref is the lowest (outlet)    
    def decideDirection(self,ref):
        if len(self.unknownNodes) != 1:
            return 0
        if not ref in self.unknownNodes:
            return 0
        if len(self.heighNodes) > 0 and len(self.lowNodes) > 0:
            return 0
        if len(self.heighNodes) > 0:
            return -1
        if len(self.lowNodes) > 0:
            return 1
        return 0
    
    def moveUnknownToHigh(self,ref):
        if ref in self.unknownNodes:
            self.unknownNodes.remove(ref)
            self.addHeighNode(ref)
        
    def moveUnknownToLow(self,ref):
        if ref in self.unknownNodes:
            self.unknownNodes.remove(ref)
            self.addLowNode(ref)
        
def setEndNodesHighLow(wayRef,highRef,lowRef,endNodes):
    if not highRef in endNodes:
        endNodes[highRef] = NodeStatus()
    endNodes[highRef].addHeighNode(wayRef)
    
    if not lowRef in endNodes:
        endNodes[lowRef] = NodeStatus()
    endNodes[lowRef].addLowNode(wayRef)
    
def setEndNodesUnknown(wayRef,nodeRef1,nodeRef2,endNodes):
    if not nodeRef1 in endNodes:
        endNodes[nodeRef1] = NodeStatus()
    if not nodeRef2 in endNodes:
        endNodes[nodeRef2] = NodeStatus()
    endNodes[nodeRef1].addUnknownNode(wayRef)
    endNodes[nodeRef2].addUnknownNode(wayRef)
    
def checkDirection(way,ways,endNodes,decidedWays):
    nd = ways[way].findall("nd")
    nd0 = nd[0].attrib["ref"]
    ndEnd = nd[-1].attrib["ref"]
    dir0 = endNodes[nd0].decideDirection(way)
    dirEnd = endNodes[ndEnd].decideDirection(way)
    if fabs(dir0+dirEnd) == 2:
        ways[way].append(etree.Element("tag", {'k':'FIXME', 'v':'Check direction of river/stream, conflicting directions'} ))
        print("Conflicting directions for way: %s" % way)
    if fabs(dir0)+fabs(dirEnd) > 0:
        decidedWays.add(way)
        if dir0 == 1 or dirEnd == -1:
            endNodes[nd0].moveUnknownToHigh(way)
            endNodes[ndEnd].moveUnknownToLow(way)
        else:
            reverseWay(ways[way], nd)
            endNodes[ndEnd].moveUnknownToHigh(way)
            endNodes[nd0].moveUnknownToLow(way)
        if dir0 == 0:
            if(len(endNodes[nd0].unknownNodes) == 1):
                for w in endNodes[nd0].unknownNodes:
                    pass
                checkDirection(w, ways, endNodes,decidedWays)
        if dirEnd == 0:
            if(len(endNodes[ndEnd].unknownNodes) == 1):
                for w in endNodes[ndEnd].unknownNodes:
                    pass
                checkDirection(w, ways, endNodes,decidedWays)
    
        
def turnTivers(fileName,fileNameOut):
    osmFile = etree.parse(fileName)
    
    ways = osmFile.xpath("way")
    nodes = nodes2nodeList(osmFile.findall("node"))
    endNodes = dict()
    wayUnknownDir = set()
    for way in ways:
        for tag in way.findall("tag"):
            if "k" in tag.attrib and tag.attrib["k"] == "waterway" and (tag.attrib["v"] == "river" or tag.attrib["v"] == "stream"):
                nd = way.findall("nd")
                if (nd[0].attrib["ref"] != nd[-1].attrib["ref"]):
                    try:
                        h1 = getElevation(nodes[nd[0].attrib['ref']])
                        h2 = getElevation(nodes[nd[-1].attrib['ref']])
                        if (fabs(h1-h2)>2):
                            if (h1 < h2):
                                reverseWay(way, nd)
                                setEndNodesHighLow(way.attrib["id"], nd[-1].attrib["ref"], nd[0].attrib["ref"], endNodes)
                            else:
                                setEndNodesHighLow(way.attrib["id"], nd[0].attrib["ref"], nd[-1].attrib["ref"], endNodes)
                        if (fabs(h1-h2)<2):
                            setEndNodesUnknown(way.attrib["id"], nd[0].attrib["ref"], nd[-1].attrib["ref"], endNodes)
                            wayUnknownDir.add(way.attrib["id"])
                            #way.append(etree.Element("tag", {'k':'FIXME', 'v':'Check direction of river/stream, elevation difference is %.1f' % int(h1-h2)} ))
                    except IndexError as e:
                        print(e)
                        #way.append(etree.Element("tag", {'k':'FIXME', 'v':'Check direction of river/stream, could not check elevation difference'} ))
                        setEndNodesUnknown(way.attrib["id"], h1.attrib["ref"], h2.attrib["ref"], endNodes)
                        wayUnknownDir.add(way.attrib["id"])
    
    ways = nodes2nodeList(ways)
    decidedWays = set()
    for way in wayUnknownDir:
        checkDirection(way,ways,endNodes,decidedWays)
    
    for way in wayUnknownDir:
        if not way in decidedWays:
            ways[way].append(etree.Element("tag", {'k':'FIXME', 'v':'Check direction of river/stream'} ))
    
    osmFile.write(fileNameOut)


if __name__ == '__main__':
    fileName = "OppdalAraldekke.osm"
    if (len(sys.argv) == 2):
        files = os.listdir(sys.argv[1])
        for f in files:
            if f.split(".")[-1] == "osm":
                print("processing %s" % f)
                fileName = os.path.join(sys.argv[1],f)
                turnTivers(fileName,fileName)
                
        
    elif (len(sys.argv) != 3):
        print("""The script requires two inputs:
Usage:
python riverTurner.py inputFile outPutfile
            
            """)
        exit()
    else:
        fileName = sys.argv[1]
        fileNameOut = sys.argv[2]
        turnTivers(fileName, fileNameOut)
