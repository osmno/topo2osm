'''
Created on Nov 29, 2014

@author: torsteinibo
'''

from lxml import etree
from mergeroads import nodes2nodeList
import sys
import os
import requests

def openOsm(fileName):
    return etree.parse(fileName)

def hashNode(node):
    return "%s:%s" %(node.attrib["lat"],node.attrib["lon"])

def hashWay(way,nodes):
    nd = way.findall("nd")
    nd0 = nodes[nd[0].attrib["ref"]]
    ndEnd = nodes[nd[-1].attrib["ref"]]
    return "%s:%d:%s" %(hashNode(nd0),len(nd),hashNode(ndEnd))

def hashRelation(relation,ways,nodes):
    member = relation.findall("member")
    way0 = ways[member[0].attrib["ref"]]
    wayEnd = ways[member[-0].attrib["ref"]]
    return "%s:%d:%s" %(hashWay(way0, nodes),len(member),hashWay(wayEnd, nodes))
    
def hashOsm(osmFile):
    nodesHashed = dict()
    for nd in osmFile.xpath("node"):
        ref = hashNode(nd)
        nodesHashed[ref] = nd
    nodes = nodes2nodeList(osmFile.xpath("node"))

    
    waysHashed = dict()
    for way in osmFile.xpath("way"):
        ref = hashWay(way,nodes)
        waysHashed[ref] = way
    ways = nodes2nodeList(osmFile.xpath("way"))    

    relationsHashed = dict()
    for rel in osmFile.xpath("relation"):
        ref = hashRelation(rel, ways, nodes)
        relationsHashed[ref] = rel
    return (nodes,nodesHashed,ways,waysHashed,relationsHashed)

def findOverlappingWay(overLapping,way,waysOsm):
    nodes = set()
    for nd in way.findall("nd"):
        nodes.add(nd.attrib["ref"])
        
    bestMatchWay = None
    bestMatchValue = -1
    
    for _,w in waysOsm.iteritems():
        match = 0
        n = 0
        for nd in w.findall("nd"):
            n += 1
            if nd.attrib["ref"] in nodes:
                match += 1
        value = match/float(n)
        if ((value > overLapping) or (match >= n - 1) or ((n > 3 and match >= n - 2)) ):
            return w
        elif (value > bestMatchValue):
            bestMatchValue = value
            bestMatchWay = w
    return bestMatchWay

def replaceWithOsm(fileName,fileNameOut,overLapping=.8):
    osmImport = openOsm(fileName)
    (nodes,nodesHashed,ways,waysHashed,relationsHashed) = hashOsm(osmImport)
    latMin = 1000.
    latMax = -latMin
    lonMin = 1000.
    lonMax = -lonMin
    for (_,nd) in nodes.iteritems():
        lat = float(nd.attrib["lat"])
        lon = float(nd.attrib["lon"])
        if lat < latMin:
            latMin = lat
        if lon < lonMin:
            lonMin = lon
        if lat > latMax:
            latMax = lat
        if lon > lonMax:
            lonMax = lon

    url = "http://www.overpass-api.de/api/xapi?*[bbox=%f,%f,%f,%f]" % (lonMin,latMin,lonMax,latMax)
    #[waterway=stream|river]
    #print url+"[@meta]"
    res = requests.get(url)
    oldOsm = etree.fromstring(res.content)
    nodesOsm = nodes2nodeList(oldOsm.xpath("node"))
    waysOsm = nodes2nodeList(oldOsm.xpath("way"))
    new2osmNodes = dict()
    for nd in oldOsm.xpath("node"):
        if hashNode(nd) in nodesHashed:
            new2osmNodes[nodesHashed[hashNode(nd)].attrib["id"]] = nd.attrib["id"]
            try:
                osmImport.getroot().remove(nodesHashed[hashNode(nd)])
            except ValueError:
                print("There is a duplicate node in OSM at position: %s %s, id: %s" %(nd.attrib["lon"],nd.attrib["lat"], nd.attrib["id"]))
    new2osmWays = dict()
    for wayOsm in oldOsm.xpath("way"):
        if hashWay(wayOsm, nodesOsm) in waysHashed:
            w = waysHashed[hashWay(wayOsm, nodesOsm)]
            new2osmWays[w.attrib["id"]] = wayOsm.attrib["id"]
            osmImport.getroot().remove(w)
    new2osmRel = dict()
    for relOsm in oldOsm.findall("relation"):
        try:
            if hashRelation(relOsm, waysOsm, nodesOsm) in relationsHashed:
                rel = relationsHashed[hashRelation(relOsm, waysOsm, nodesOsm)]
                new2osmRel[rel.attrib["id"]] = relOsm.attrib["id"]
                osmImport.getroot().remove(rel)
        except KeyError:
            pass
    
    for ref, way in ways.iteritems():
        if not ref in new2osmWays:
            nInOsm = 0
            nNodes = 0
            for nd in way.findall("nd"):
                nNodes += 1
                if nd.attrib["ref"] in new2osmNodes:
                    nd.attrib["ref"] = new2osmNodes[nd.attrib["ref"]]
                    nInOsm += 1
            if nInOsm/float(nNodes) > .9 or nInOsm >= nNodes - 1 or (nNodes > 2 and nInOsm >= nNodes - 2) :
                # Many of the nodes are in OSM already, the way is allready imported
                w = findOverlappingWay(overLapping,way,waysOsm)
                new2osmWays[ref] = w.attrib["id"]
                osmImport.getroot().remove(way)
    
    for ref, rel in relationsHashed.iteritems():
        if not ref in new2osmWays:
            for member in rel.findall("member"):
                if member.attrib["type"] == "way":
                    if member.attrib["ref"] in new2osmWays:
                        member.attrib["ref"] = new2osmWays[member.attrib["ref"]]
                elif member.attrib["type"] == "node":
                    if member.attrib["ref"] in new2osmNodes:
                        member.attrib["ref"] = new2osmNodes[member.attrib["ref"]]
                else:
                    raise Warning("Type of member in relation unknown (id %d)" % rel.attrib["id"])
    
    osmImport.write(fileNameOut)
    #(nodes,nodesHashed,ways,waysHashed,relationsHashed) = hashOsm(oldOsm)

if __name__ == '__main__':
    fileName = None
    if (len(sys.argv) == 2):
        files = os.listdir(sys.argv[1])
        for f in files:
            if f.split(".")[-1] == "osm":
                print("processing %s" % f)
                fileName = os.path.join(sys.argv[1],f)
                osmImport = openOsm(fileName)
                
                
        
    elif (len(sys.argv) != 3):
        print("""The script requires two inputs:
Usage:
python replaceWithOsm.py inputFile outPutfile
            
            """)
        exit()
    else:
        fileName = sys.argv[1]
        fileNameOut = sys.argv[2]
        replaceWithOsm(fileName, fileNameOut)
