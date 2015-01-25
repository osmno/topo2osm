'''
Created on Nov 29, 2014

@author: torsteinibo
'''

from lxml import etree
from mergeroads import nodes2nodeList
import sys
import os
import requests
from riverTurner import reverseWay

def openOsm(fileName):
    return etree.parse(fileName)

def hashNode(node):
    return "%.7f:%.7f" %(float(node.attrib["lat"]),float(node.attrib["lon"]))

def hashWay(way,nodes):
    nd = way.findall("nd")
    hashStr = ""
    for nd in way.findall("nd"):
        hashStr = "%s:%s" % (hashStr, hashNode(nodes[nd.attrib["ref"]]))
    return hashStr

def reverseHashWay(way,nodes):
    nd = way.findall("nd")
    hashStr = ""
    for nd in way.findall("nd"):
        hashStr = "%s:%s" % (hashNode(nodes[nd.attrib["ref"]]),hashStr)
    return hashStr

def hashRelation(relation,ways,nodes):
    hashStr = ""
    for memb in relation.findall("member"):
        hashStr = "%s:%s" % (hashStr,hashWay(ways[memb.attrib["ref"]], nodes))
    return hashStr

def copyTags(fromE,toE):
    for tag in fromE.findall("tag"):
        if "k" in tag.attrib and not (tag.attrib["k"] == "source:date") :
            toE.append(tag)
    
def hashOsm(osmFile):
    nodesHashed = dict()
    newNode = dict()
    for nd in osmFile.xpath("node"):
        ref = hashNode(nd)
        if ref in nodesHashed:
            newNode[nd.attrib["id"]] = nodesHashed[ref].attrib["id"]
            copyTags(nd, nodesHashed[ref])
            osmFile.getroot().remove(nd)
        else:
            nodesHashed[ref] = nd
    nodes = nodes2nodeList(osmFile.xpath("node"))
    
    
    waysHashed = dict()
    for way in osmFile.xpath("way"):
        for nd in way.findall("nd"):
            ref = nd.attrib["ref"]
            if ref in newNode:
                nd.attrib["ref"] =  newNode[ref]
        ref = hashWay(way,nodes)
        if ref in waysHashed:
            raise ValueError("Two ways have same hash: %s" % ref)
        waysHashed[ref] = way
        ref = reverseHashWay(way,nodes)
        if ref in waysHashed:
            raise ValueError("Two ways have same hash: %s" % ref)
        waysHashed[ref] = way
        
        
    ways = nodes2nodeList(osmFile.xpath("way"))    

    relationsHashed = dict()
    for rel in osmFile.xpath("relation"):
        ref = hashRelation(rel, ways, nodes)
        if ref in relationsHashed:
            raise ValueError("Two relation have same hash: %s" % ref)
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
        nodesCandidate = w.findall("nd")
        if (abs(len(nodesCandidate)-len(nodes)) < (1-overLapping)*len(nodes) ):
            for nd in nodesCandidate:
                n += 1
                if nd.attrib["ref"] in nodes:
                    match += 1
            value = match/float(n)
            if (value > overLapping):
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

    url = "http://www.overpass-api.de/api/xapi?*[bbox=%f,%f,%f,%f][@meta]" % (lonMin,latMin,lonMax,latMax)
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
            newWay = waysHashed[hashWay(wayOsm, nodesOsm)]
            new2osmWays[newWay.attrib["id"]] = wayOsm.attrib["id"]
            #check if tags are equal
            oldTag = set()
            for t in wayOsm.findall("tag"):
                oldTag.add(t.attrib["k"]+t.attrib["v"])
            newTags = set()
            for t in newWay.findall("tag"):
                if (t.attrib["k"] != "source:date" and (t.attrib["k"]+t.attrib["v"]) not in oldTag):
                    newTags.add(t)           
            try:
                osmImport.getroot().remove(newWay)
            except ValueError:
                print("There is a duplicate way with id: %s" %(wayOsm.attrib["id"]))
                
            if (len(newTags) > 0):
                wayOsm.attrib["action"] = "modify"
                for t in newTags:
                    wayOsm.append(t)
                if hashWay(wayOsm, nodesOsm) == reverseHashWay(newWay, nodes):
                    reverseHashWay(wayOsm)
                osmImport.getroot().append(wayOsm)
        else:
            shouldBeIncluded = False
            for tag in wayOsm.findall("tag"):
                k = tag.attrib["k"]
                v = tag.attrib["v"]
                if ((k == "natural" and v == "water") or (k == "waterway")):
                    shouldBeIncluded = True
                    break
            if shouldBeIncluded:
                wayOsm.append(etree.Element("tag", {'k':'FIXME', 'v':'Merge'} ))
                wayOsm.attrib["action"] = "modify"
                osmImport.getroot().append(wayOsm)
    new2osmRel = dict()
    for relOsm in oldOsm.findall("relation"):  
        try:
            hashStr = hashRelation(relOsm, waysOsm, nodesOsm)
        except KeyError:
            hashStr = None
        if hashStr in relationsHashed:
            #candRel = relationsHashed[hashRelation(relOsm, waysOsm, nodesOsm)]
#             candMem = set()
#             for cMem in candRel.findall("member"):
#                 if (cMem.attrib["type"] == "node"):
#                     candMem.add(hashNode(nodes[cMem.attrib["ref"]]))
#                 else:
#                     candMem.add(hashWay(ways[cMem.attrib["ref"]], nodes))
#             equalRel = True
#             for mem in relOsm.findall("member"):
#                 if mem.attrib["type"] == "node" and (not hashNode(nodesOsm[mem.attrib["ref"]]) in candMem):
#                     equalRel = False
#                     break
#                 elif mem.attrib["type"] == "way" and (not hashWay(waysOsm[mem.attrib["ref"]], nodesOsm) in candMem):
#                     equalRel = False
#                     break
            #if equalRel:
            rel = relationsHashed[hashRelation(relOsm, waysOsm, nodesOsm)]
            new2osmRel[rel.attrib["id"]] = relOsm.attrib["id"]
            try:
                osmImport.getroot().remove(rel)
            except KeyError:
                print("There is a duplicate relation with id: %s" %(relOsm.attrib["id"]))
        else:
            shouldBeIncluded = False
            for tag in relOsm.findall("tag"):
                k = tag.attrib["k"]
                v = tag.attrib["v"]
                if ((k == "natural" and v == "water") or (k == "waterway")):
                    shouldBeIncluded = True
                    break
            if shouldBeIncluded:
                relOsm.append(etree.Element("tag", {'k':'FIXME', 'v':'Merge'} ))
                relOsm.attrib["action"] = "modify"
                osmImport.getroot().append(relOsm)
    
    for ref, way in ways.iteritems():
        if not ref in new2osmWays:
#             nInOsm = 0
#             nNodes = 0
            for nd in way.findall("nd"):
#                 nNodes += 1
                if nd.attrib["ref"] in new2osmNodes:
                    nd.attrib["ref"] = new2osmNodes[nd.attrib["ref"]]
#                     nInOsm += 1
#             if nInOsm/float(nNodes) > .9 or (nNodes>2 and nInOsm >= nNodes - 1) or (nNodes > 4 and nInOsm >= nNodes - 2) :
#                 # Many of the nodes are in OSM already, the way is allready imported
#                 w = findOverlappingWay(overLapping,way,waysOsm)
#                 new2osmWays[ref] = w.attrib["id"]
#                 osmImport.getroot().remove(way)
#     
    for rel in osmImport.xpath("relation"):
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
