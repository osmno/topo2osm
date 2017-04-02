'''
Created on Nov 29, 2014

@author: torsteinibo
'''

from lxml import etree
from mergeroads import nodes2nodeList
from misc import equalTags, combineWays, reLinkRef
import sys


# Class for wrapping and combining ways
# class wayWrapper:
#     bBoxN = -90.
#     bBoxE = -180.
#     bBoxS = 90.
#     bBoxW = 180.        
#     def __init__(self,element,nodes):
#         for nd in element.findall("nd"):
#             n = nodes[nd.attrib['ref']]
#             lat = float(n.attrib["lat"])
#             lon = float(n.attrib["lon"])
#             self.bBoxN = max(self.bBoxN,lat)
#             self.bBoxS = min(self.bBoxS,lat)
#             self.bBoxW = min(self.bBoxW,lon)
#             self.bBoxE = max(self.bBoxE,lon)
            

def simplifyWay(fileName,fileNameOut):
    osmFile = etree.parse(fileName)
    
    relations = nodes2nodeList(osmFile.getroot().findall("relation"))
    ways = nodes2nodeList(osmFile.getroot().findall("way"))
    waysToRelation = dict()
    for ref,rel in relations.iteritems():
        members = rel.findall("member")
        for w in members:
            wRef = w.attrib["ref"]
            if wRef not in waysToRelation:
                waysToRelation[wRef] = set()
            waysToRelation[wRef].add(ref)
    
    startNodeToWay = dict()
    endNodeToWay = dict()
    for ref, w in ways.iteritems():
        nd = w.findall("nd")
        startNode = nd[0].attrib["ref"]
        endNode = nd[-1].attrib["ref"]
        
        # Check if way has FIXME="Check direction of river/stream"
        ignore = False
        for t in w.findall("tag"):
            k = t.attrib["k"]
            v = t.attrib["v"]
            if (k == "FIXME" and v == "Check direction of river/stream"):
                ignore = True
                break
        
        
        if startNode != endNode and not ignore:
            if endNode in startNodeToWay:
                for candRef in startNodeToWay[endNode]:
                    tagsEqual = equalTags(ways[candRef],ways[ref])
                    equalRel = (ref in waysToRelation and candRef in waysToRelation)
                    if (equalRel):
                        equalRel = waysToRelation[ref] ==  waysToRelation[candRef]
                    else:
                        equalRel = (ref not in waysToRelation and candRef not in waysToRelation)
                    if tagsEqual and equalRel:
                        combineWays(osmFile.getroot(),w,ways[candRef])
                        if (candRef in waysToRelation):
                            reLinkRef(waysToRelation[candRef],relations,candRef)
                        startNodeToWay[endNode].remove(candRef)
                        endNode = w.findall("nd")[-1].attrib["ref"]
                        endNodeToWay[endNode].remove(candRef)
                        ways[candRef] = None
                        break
            if endNode not in endNodeToWay:
                endNodeToWay[endNode] = set()
            endNodeToWay[endNode].add(ref)
            
            combined = False
            if startNode in endNodeToWay:
                for candRef in endNodeToWay[startNode]:
                    if candRef != ref:
                        tagsEqual = equalTags(ways[candRef],w)
                        equalRel = (ref in waysToRelation and candRef in waysToRelation)
                        if (equalRel):
                            equalRel = waysToRelation[ref] ==  waysToRelation[candRef]
                        else:
                            equalRel = (ref not in waysToRelation and candRef not in waysToRelation)
                        if tagsEqual and equalRel:
                            combined = True
                            combineWays(osmFile.getroot(),ways[candRef],w)
                            if (ref in waysToRelation):
                                reLinkRef(waysToRelation[ref],relations,ref)
                            endNodeToWay[startNode].remove(candRef)
                            endNodeToWay[endNode].remove(ref)
                            endNodeToWay[endNode].add(candRef)
                            ways[ref] = None
                            break
            if not combined:
                if startNode not in startNodeToWay:
                    startNodeToWay[startNode] = set()
                startNodeToWay[startNode].add(ref)
        
        startNodesRefs = set()
        endNodesRefs= set()
        for _, waysRefs in startNodeToWay.iteritems():
            for wref in waysRefs:
                assert(wref not in startNodesRefs)
                startNodesRefs.add(wref)
        for _, waysRefs in endNodeToWay.iteritems():
            for wref in waysRefs:
                assert(wref not in endNodesRefs)
                endNodesRefs.add(wref)
        
        assert(startNodesRefs == endNodesRefs)
            

                    
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
        simplifyWay(fileName, fileNameOut)
