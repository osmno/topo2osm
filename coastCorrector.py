'''
Created on Nov 29, 2014

@author: torsteinibo
'''

from lxml import etree
from misc import reverseWay
from nodes2nodeList import nodes2nodeList
import sys
from math import atan2, pi


# Class for wrapping and combining ways
class wayWrapper:
    ways = None
    startNode = None
    endNode = None
    def __init__(self,way):
        self.ways = [way]
        nd = way.findall("nd")
        self.startNode = int(nd[0].attrib["ref"])
        self.endNode = int(nd[-1].attrib["ref"])
    def addWayToStart(self,way):
        assert(way.endNode == self.startNode)
        self.ways = way.ways+self.ways
        self.startNode = way.startNode
    def addWayToEnd(self,way):
        assert(self.endNode == way.startNode)
        self.ways = way.ways+self.ways
        self.endNode = way.endNode
    def merge(self,way):
        startNode = way.startNode
        endNode = way.endNode
        if startNode == self.startNode:
            way.reverse()
            self.addWayToStart(way)
        elif startNode == self.endNode:
            self.addWayToEnd(way)
        elif endNode == self.startNode:
            self.addWayToStart(way)
        elif endNode == self.endNode:
            way.reverse()
            self.addWayToEnd(way)

        return self.startNode == self.endNode
    def combine(self,otherWrapper):
        assert(self.endNode == otherWrapper.startNode)
        self.ways = self.ways + otherWrapper.ways
        self.endNode = otherWrapper.endNode
    def reverse(self):
        for w in self.ways:
            reverseWay(w)
        tmp = self.startNode
        self.startNode = self.endNode
        self.endNode = tmp
            
    def touch(self,way):
        startNode = way.startNode
        endNode = way.endNode
        return (startNode == self.startNode) or (startNode == self.endNode) or (endNode == self.startNode) or (endNode == self.endNode)


def getSumOfAngles(ways,nodes):
    nd = ways[-1].findall('nd')
    nd0 = nodes[nd[-2].attrib["ref"]]
    nd1 = nodes[nd[-1].attrib["ref"]]
    dlat =float(nd1.attrib["lat"]) - float(nd0.attrib["lat"])
    dlon =float(nd1.attrib["lon"]) - float(nd0.attrib["lon"])
    ang1 = atan2(dlat,dlon)
    ang0 = None
    sumAngle = 0

    
    for w in ways:
        for nd in w.findall("nd")[1:]:
            ang0 = ang1+pi
            nd0 = nd1
            nd1 = nodes[nd.attrib["ref"]]
            dlat =float(nd1.attrib["lat"]) - float(nd0.attrib["lat"])
            dlon =float(nd1.attrib["lon"]) - float(nd0.attrib["lon"])
            ang1 = atan2(dlat,dlon)
            a = (ang0-ang1) % (2*pi)
            a = a - (a>pi)*(2*pi)
            assert a <= pi and a >= -pi, a 
            sumAngle += a    
    return sumAngle

def coastCorrector(fileName,fileNameOut):
    osmFile = etree.parse(fileName)
    nodes = nodes2nodeList(osmFile.findall("node"))
    ways = dict()
    
    i = 0
    for w in osmFile.findall("way"):
        ways[i]= wayWrapper(w)
        i += 1
    
    nWays = i
    
    didMerge = True
    while didMerge:
        didMerge = False
        for i in range(nWays):
            if ways[i] is not None:
                for j in range(nWays):
                    if (i != j) and (ways[j] is not None) and (ways[i].touch(ways[j])):
                        ways[i].merge(ways[j])
                        ways[j] = None
                        didMerge = True
    
    i = 0
    for w in ways.itervalues():
        if w is not None:
            if w.startNode != w.endNode:
                print "Way not in circle"
                for iw in w.ways:
                    iw.append(etree.Element("tag", {'k':'FIXME', 'v':'Check direction of coastline. Land should be on the left side and water on the right side.'} ))
            elif getSumOfAngles(w.ways, nodes) < 0:
                w.reverse()

                    
    osmFile.write(fileNameOut)


if __name__ == '__main__':
    fileName = None
    if (len(sys.argv) < 3):
        print("""The script requires two inputs:
Usage:
python riverTurner.py inputFile outPutfile
            
            """)
        exit()
    else:
        fileName = sys.argv[1]
        fileNameOut = sys.argv[2]
        coastCorrector(fileName, fileNameOut)
