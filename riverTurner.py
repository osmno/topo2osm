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
        self.highNodes = set()
        self.unknownNodes = set()
        
    def addLowNode(self,ref):
        self.lowNodes.add(ref)
        
    def addHighNode(self,ref):
        self.highNodes.add(ref)
        
    def addUnknownNode(self,ref):
        self.unknownNodes.add(ref)
        
    def copy(self,copy):
        self.lowNodes = self.lowNodes.union(copy.lowNodes)
        self.highNodes = self.highNodes.union(copy.highNodes)
        self.unknownNodes = self.unknownNodes.union(copy.unknownNodes)
    
    # Returns 1 if ref is the highest (inlet)
    # Returns 0 if unknown
    # Returns -1 if ref is the lowest (outlet)    
    def decideDirection(self,ref):
        if len(self.unknownNodes) != 1:
            return 0
        if not ref in self.unknownNodes:
            return 0
        if len(self.highNodes) > 0 and len(self.lowNodes) > 0:
            return 0
        if len(self.highNodes) > 0:
            return -1
        if len(self.lowNodes) > 0:
            return 1
        return 0
    
    def moveUnknownToHigh(self,ref):
        if ref in self.unknownNodes:
            self.unknownNodes.remove(ref)
            self.addHighNode(ref)
        
    def moveUnknownToLow(self,ref):
        if ref in self.unknownNodes:
            self.unknownNodes.remove(ref)
            self.addLowNode(ref)

class EndNodes:
    store = None
    def __init__(self):
        self.store = dict()
    def setEndNodesHighLow(self,wayRef,highRef,lowRef):
        if not highRef in self.store:
            self.store[highRef] = NodeStatus()
        self.store[highRef].addHighNode(wayRef)
        
        if not lowRef in self.store:
            self.store[lowRef] = NodeStatus()
        self.store[lowRef].addLowNode(wayRef)
    
    def setEndNodesUnknown(self,wayRef,nodeRef1,nodeRef2):
        if not nodeRef1 in self.store:
            self.store[nodeRef1] = NodeStatus()
        if not nodeRef2 in self.store:
            self.store[nodeRef2] = NodeStatus()
        self.store[nodeRef1].addUnknownNode(wayRef)
        self.store[nodeRef2].addUnknownNode(wayRef)
        
    def __setitem__(self, k, v):
        self.store[k] = v
    
    def __getitem__(self,k):
        return self.store[k]
    
    def __delitem__(self,k):
        del self.store[k]
        
    def __contains__(self,k):
        return k in self.store
    
def checkDirection(way,ways,endNodes,decidedWays,nodesToCircularWay):
    nd = ways[way].findall("nd")
    nd0 = nd[0].attrib["ref"]
    ndEnd = nd[-1].attrib["ref"]
    if nd0 in nodesToCircularWay:
        nd0 = nodesToCircularWay[nd0]

    dir0 = endNodes[nd0].decideDirection(way)
        
    if ndEnd in nodesToCircularWay:
        ndEnd = nodesToCircularWay[ndEnd]
    
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
                checkDirection(w, ways, endNodes,decidedWays,nodesToCircularWay)
        if dirEnd == 0:
            if(len(endNodes[ndEnd].unknownNodes) == 1):
                for w in endNodes[ndEnd].unknownNodes:
                    pass
                checkDirection(w, ways, endNodes,decidedWays,nodesToCircularWay)
    
def turnRivers(fileName,fileNameOut):
    osmFile = etree.parse(fileName)
    
    ways = osmFile.xpath("way")
    nodes = nodes2nodeList(osmFile.findall("node"))
    endNodes = EndNodes()
    wayUnknownDir = set()
    wayCircular = set()
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
                                endNodes.setEndNodesHighLow(way.attrib["id"], nd[-1].attrib["ref"], nd[0].attrib["ref"])
                            else:
                                endNodes.setEndNodesHighLow(way.attrib["id"], nd[0].attrib["ref"], nd[-1].attrib["ref"])
                        if (fabs(h1-h2)<2):
                            endNodes.setEndNodesUnknown(way.attrib["id"], nd[0].attrib["ref"], nd[-1].attrib["ref"])
                            wayUnknownDir.add(way.attrib["id"])
                            #way.append(etree.Element("tag", {'k':'FIXME', 'v':'Check direction of river/stream, elevation difference is %.1f' % int(h1-h2)} ))
                    except IndexError as e:
                        print(e)
                        #way.append(etree.Element("tag", {'k':'FIXME', 'v':'Check direction of river/stream, could not check elevation difference'} ))
                        endNodes.setEndNodesUnknown(way.attrib["id"], h1.attrib["ref"], h2.attrib["ref"])
                        wayUnknownDir.add(way.attrib["id"])
                else:
                    wayCircular.add(way.attrib["id"])
                    
                    

    
    
    ways = nodes2nodeList(ways)
    
    nodesToCircularWay = dict()
    for rel in osmFile.xpath("relation"):
        isWater = False
        for tag in rel.findall("tag"):
            if tag.attrib["k"] == "waterway" or (tag.attrib["k"] == "natural" and tag.attrib["v"] == "water"):
                isWater = True
        if isWater:
            ref = rel.attrib["id"]+"r"
            ndStatus = NodeStatus()
            for way in rel.findall("member"):
                if way.attrib["role"] == "outer":
                    for nd in ways[way.attrib["ref"]].findall("nd"):
                        ndRef = nd.attrib["ref"]
                        if ndRef in endNodes:
                            ndStatus.copy(endNodes[ndRef])
                            del endNodes[ndRef]
                            nodesToCircularWay[ndRef] = ref
            endNodes[ref] = ndStatus
         
    
                
    
    decidedWays = set()
    for way in wayUnknownDir:
        checkDirection(way,ways,endNodes,decidedWays,nodesToCircularWay)
    
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
                turnRivers(fileName,fileName)
                
        
    elif (len(sys.argv) != 3):
        print("""The script requires two inputs:
Usage:
python riverTurner.py inputFile outPutfile
            
            """)
        exit()
    else:
        fileName = sys.argv[1]
        fileNameOut = sys.argv[2]
        turnRivers(fileName, fileNameOut)
