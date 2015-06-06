'''
Created on Nov 29, 2014

@author: torsteinibo
'''

from lxml import etree
from nodes2nodeList import nodes2nodeList
import sys
from copy import deepcopy


def openOsm(fileName):
    return etree.parse(fileName)

class Splitter:
    def __init__(self,_osmFile,latMin,latMax,lonMin,lonMax,keepAdjacentWays):
        self.osmFile = _osmFile
        element = etree.fromstring('<?xml version="1.0"?><osm/>')
        element.attrib.update(_osmFile.getroot().attrib)
        self.splitFile = etree.ElementTree(element)
        
        self.keepAdjacentWays = keepAdjacentWays
        self.latMin = latMin
        self.latMax = latMax
        self.lonMin = lonMin
        self.lonMax = lonMax
        
        self.node = nodes2nodeList(self.osmFile.getroot().findall("node"))
        self.way = nodes2nodeList(self.osmFile.getroot().findall("way"))
        self.relation = nodes2nodeList(self.osmFile.getroot().findall("relation"))
        
        
        
        nd2wref = dict()
        for wref,w in self.way.iteritems():
            for nd in w.findall("nd"):
                ref = nd.attrib["ref"]
                if ref not in nd2wref:
                    nd2wref[ref] = set()
                nd2wref[ref].add(wref)
        self.nd2wref = nd2wref
        
        
        
        w2relref = dict()
        for relRef,rel in self.relation.iteritems():
            for w in rel.findall("mem"):
                ref = w.attrib["ref"]
                if ref not in nd2wref:
                    w2relref[ref] = set()
                w2relref[ref].add(relRef)
        self.w2relref = w2relref

        
        self.inNdExpanding = set()
        self.inWayExpanding = set()
        self.inRelationExpanding = set()
        
        self.inSplitNode = set()
        self.inSplitWay = set()
        self.inSplitRelation = set()
        
        
        # Copy nodes, ways and relations from osm to split
        for ref,nd in self.node.iteritems():
            if self.isNdInBbox(ref, nd):
                self.addNodeToSplit(ref)
        

        # Remove nodes, ways and relations duplicate from osm        
        wayOsm = dict()
        for ref,way in self.way.iteritems():
            wayOsm[ref] = way
        
        relOsm = dict()
        for ref,rel in self.relation.iteritems():
            relOsm[ref] = rel
        
        
        
        for ref in self.inSplitRelation:
            self.osmFile.getroot().remove(relOsm[ref])
            del relOsm[ref]

        for ref in self.inSplitWay:
            delete = True
            if ref in self.w2relref:
                for relRef in self.w2relref[ref]:
                    if relRef in relOsm:
                        delete = False
                        break
            if delete:
                self.osmFile.getroot().remove(self.way[ref])
                del wayOsm[ref]
                
        for ref in self.inSplitNode:
            delete = True
            if ref in self.nd2wref:
                for wRef in self.nd2wref[ref]:
                    if wRef in wayOsm:
                        delete = False
                        break
            if delete:
                self.osmFile.getroot().remove(self.node[ref])
            

                
    def isNdInBbox(self,ndRef,nd = None):
        if nd is None:
            nd = self.node[ndRef]
        lat = float(nd.attrib["lat"])
        lon = float(nd.attrib["lon"])
        return lat <= self.latMin or lat >= self.latMax or lon <= self.lonMin or lon >= self.lonMax
    
    
    def addNodeToSplit(self,ref,expand = None,node=None):

        if (node is None):
            node = self.node[ref]
        
        if expand is None:
            expand = self.keepAdjacentWays or self.isNdInBbox(ref,node)
        elif self.keepAdjacentWays:
            expand = True 
        
        if (ref in self.inSplitNode and (expand == False or (ref in self.inNdExpanding))):
            return
        
        if expand:
            self.inNdExpanding.add(ref)
        
        self.inSplitNode.add(ref)
        self.splitFile.getroot().append(deepcopy(node))
        if expand:
            if ref in self.nd2wref:
                for wRef in self.nd2wref[ref]:
                    self.addWayToSplit(wRef,True)

    
    def addWayToSplit(self,wRef,expand):
        if (wRef in self.inSplitWay and (expand == False or (wRef in self.inWayExpanding))):
            return

        self.inSplitWay.add(wRef)
        
        if expand:
            self.inWayExpanding.add(wRef)
        
        way = self.way[wRef]
        self.splitFile.getroot().append(deepcopy(way))

        if expand:
            if wRef in self.w2relref:
                for relRef in self.w2relref[wRef]:
                    self.addRelationToSplit(relRef)
                    
        for nd in way.findall("nd"):
            self.addNodeToSplit(nd.attrib["ref"], False)
                    
    def addRelationToSplit(self,ref):
        if (ref in self.inSplitRelation):
            return

        self.inSplitRelation.add(ref)
        
        rel = self.relation[ref]
        self.splitFile.append(deepcopy(rel))
        
        for w in rel.findall("member"):
            self.iterateNodeToSplit(w.attrib["ref"], False)


def myround(x, base):
    return base * round(x/base)

def saveFile(latMin,latMax,lonMin,lonMax,osmFile,fileNameOut):
    if len(osmFile.getroot()) == 0:
        return
    osmFile.write("%s_%.2f_%.2f_%.2f_%.2f.osm" % (fileNameOut,latMin,latMax,lonMin,lonMax)) 
    
def splitter(osmFile,latMin,latMax,lonMin,lonMax,keepAdjacentWays):
    s = Splitter(osmFile,latMin,latMax,lonMin,lonMax,keepAdjacentWays)
    return (s.osmFile,s.splitFile)

def recursiveSplit(latMin,latMax,lonMin,lonMax,osmFile,fileNameOut,keepAdjacentWays):
    if (latMax-latMin) <= .05 and (lonMax-lonMin) <= .05:
        saveFile(latMin,latMax,lonMin,lonMax,osmFile,fileNameOut)
    elif len(osmFile.getroot().findall("node")) < 20000:
        saveFile(latMin,latMax,lonMin,lonMax,osmFile,fileNameOut)
    elif (latMax-latMin) < (lonMax-lonMin):
        lonMed = myround((lonMax-lonMin)/2,dx)+lonMin
        (split1, split2) = splitter(osmFile, -180, 180, -180, lonMed,keepAdjacentWays)
        recursiveSplit(latMin,latMax,lonMin,lonMed,split1,fileNameOut,keepAdjacentWays)
        recursiveSplit(latMin,latMax,lonMed,lonMax,split2,fileNameOut,keepAdjacentWays)
    else:
        latMed = myround((latMax-latMin)/2,dx)+latMin
        (split1, split2) = splitter(osmFile,-180, latMed, -180, 180,keepAdjacentWays)
        recursiveSplit(latMin,latMed,lonMin,lonMax,split1,fileNameOut,keepAdjacentWays)
        recursiveSplit(latMed,latMax,lonMin,lonMax,split2,fileNameOut,keepAdjacentWays)
    

if __name__ == '__main__':
    fileName = None
    usage = """The script requires two or three inputs:
Usage:
python splitterOsm.py inputFile outputFilePrefix [--keepAdjacentWays]
            
Error: %s            """
    if (len(sys.argv) < 3):
        print(usage % ("Only %d inputs was given" % (len(sys.argv)-1)))
        exit()
    if len(sys.argv) > 4:
        print(usage % ("%d inputs was given" % (len(sys.argv)-1)))
        exit()
    else:
        fileName = sys.argv[1]
        fileNameOut = sys.argv[2]
        
        keepAdjacentWays = False
        if len(sys.argv) == 4:
            if sys.argv[3] == "--keepAdjacentWays":
                keepAdjacentWays = True
            else:
                print(usage  % "The flag is not valid")
                exit()
        
            

        osmFile = openOsm(fileName)
        latMin = 180
        latMax = -180
        lonMin = 180
        lonMax = -180
        for node in osmFile.getroot().findall("node"):
            lat = float(node.attrib["lat"])
            lon = float(node.attrib["lon"])
            latMin = min(lat,latMin)
            lonMin = min(lon,lonMin)
            latMax = max(lat,latMax)
            lonMax = max(lon,lonMax)
        
        dx = .05
        latMin = latMin - latMin % dx
        lonMin = lonMin - lonMin % dx
        latMax = latMax + (dx-latMax % dx)
        lonMax = lonMax + (dx-lonMax % dx)
        recursiveSplit(latMin,latMax,lonMin,lonMax,osmFile,fileNameOut,keepAdjacentWays)

