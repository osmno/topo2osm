#!/usr/bin/env python
'''
Created on Nov 29, 2014

@author: torsteinibo
'''

from lxml import etree as ET
import sys
import requests
from misc import reverseWay

def nodes2nodeList(nodes):
    l = {}
    for n in nodes:
        l[n.attrib['id']] = n
    return l

def openOsm(fileName):
    return ET.parse(fileName)

def hashNode(node):
    return "%.7f:%.7f" %(float(node.attrib["lat"]),float(node.attrib["lon"]))

def hashWay(way,nodes):
    nd = way.findall("nd")
    hashStr = ""
    for nd in way.findall("nd"):
        hashStr = "%s:%s" % (hashStr, hashNode(nodes[nd.attrib["ref"]]))
    return hashStr[1:]

def reverseHashWay(way,nodes):
    nd = way.findall("nd")
    hashStr = ""
    for nd in way.findall("nd"):
        hashStr = "%s:%s" % (hashNode(nodes[nd.attrib["ref"]]),hashStr)
    return hashStr[:-1]

def hashRelation(relation,ways,nodes):
    hashStr = ""
    for memb in relation.findall("member"):
        hashStr = "%s:%s" % (hashStr,hashWay(ways[memb.attrib["ref"]], nodes))
    return hashStr

def hasConflictingTags(fromE,toE):
    tags = dict()
    for tag in fromE.findall("tag"):
        if (tag.attrib["k"] != "source:date") :
            tags[tag.attrib["k"]] = tag.attrib["v"]

    for tag in toE.findall("tag"):
        if tag.attrib["k"] in tags and tags[tag.attrib["k"]] != tag.attrib["v"]:
            return True

    return False

def copyTags(fromE,toE):
    for tag in fromE.findall("tag"):
        if "k" in tag.attrib and not (tag.attrib["k"] == "source:date") :
            toE.append(tag)
    
def hashOsm(osmFile):
    nodesHashed = dict()
    newNode = dict()
    for nd in osmFile.getroot().findall("node"):
        ref = hashNode(nd)
        if ref in nodesHashed:
            newNode[nd.attrib["id"]] = nodesHashed[ref].attrib["id"]
            copyTags(nd, nodesHashed[ref])
            osmFile.getroot().remove(nd)
        else:
            nodesHashed[ref] = nd
    nodes = nodes2nodeList(osmFile.getroot().findall("node"))
    
    
    waysHashed = dict()
    for way in osmFile.getroot().findall("way"):
        for nd in way.findall("nd"):
            ref = nd.attrib["ref"]
            if ref in newNode:
                nd.attrib["ref"] =  newNode[ref]
        ref = hashWay(way,nodes)
        if len(ref) == 0:
            raise ValueError("There is an empty way with id: %s. Remove this way and try again." % way.attrib['id'])
        if ref in waysHashed:
            raise ValueError("Two ways have the same nodes. Remove duplicates and try again. The ids are: %s and %s. The nodes are: %s" % (way.attrib['id'], waysHashed[ref].attrib['id'],ref))
        waysHashed[ref] = way
        ref = reverseHashWay(way,nodes)
        if ref in waysHashed:
            raise ValueError("Two ways have the same nodes. Remove duplicates and try again. The ids are: %s and %s. The nodes are: %s" % (way.attrib['id'], waysHashed[ref].attrib['id'],ref))
        waysHashed[ref] = way
        
        
    ways = nodes2nodeList(osmFile.getroot().findall("way"))    

    relationsHashed = dict()
    for rel in osmFile.getroot().findall("relation"):
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

def replaceWithOsm(fileName,fileNameOut,importAreal,importWater,importWay,overLapping=.8):
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
            
    minRelationId = -1;
    for _,rel in relationsHashed.iteritems():
        minRelationId = min(minRelationId,int(rel.attrib['id']))
        
    
    bbox = "%f,%f,%f,%f" %(lonMin,latMin,lonMax,latMax)
    url = "http://www.overpass-api.de/api/xapi?*[bbox=%s][@meta]" % bbox
    #[waterway=stream|river]
    if importWay:
        bbox = "%f,%f,%f,%f" %(latMin,lonMin,latMax,lonMax)
        url = 'http://overpass-api.de/api/interpreter?data=(way(%s)["highway"];node(%s)["barrier"];);(._;>;);out meta;' % (bbox,bbox)
        print url
    res = requests.get(url)
    oldOsm = ET.fromstring(res.content)
    nodesOsm = nodes2nodeList(oldOsm.findall("node"))
    waysOsm = nodes2nodeList(oldOsm.findall("way"))
    new2osmNodes = dict()
    includedNodes = set()
    for nd in oldOsm.findall("node"):
        if hashNode(nd) in nodesHashed:
            new2osmNodes[nodesHashed[hashNode(nd)].attrib["id"]] = nd.attrib["id"]
            try:
                osmImport.getroot().remove(nodesHashed[hashNode(nd)])
            except ValueError:
                print("There is a duplicate node in OSM at position: %s %s, id: %s" %(nd.attrib["lon"],nd.attrib["lat"], nd.attrib["id"]))
        if importCoastline:
            shouldBeIncluded = False
            fromN50 = False
            for tag in nd.findall("tag"):
                k = tag.attrib["k"]
                v = tag.attrib["v"]
                if ((k == "natural" and v == "coastline") or (k=="seamark:type" and v != "light_minor")):
                    shouldBeIncluded = True
                if k=="source" and (v=="Kartverket N50" or v=="Kartverket" or v=="Statkart"):
                    fromN50 = True
            if shouldBeIncluded:
                if not fromN50:
                    nd.append(ET.Element("tag", {'k':'FIXME', 'v':'Merge'} ))
                    nd.attrib["action"] = "modify"
                osmImport.getroot().append(nd)
                includedNodes.add(nd.attrib["id"])
    new2osmWays = dict()
    
    includedWays = set()
    for wayOsm in oldOsm.findall("way"):
        if hashWay(wayOsm, nodesOsm) in waysHashed:
            newWay = waysHashed[hashWay(wayOsm, nodesOsm)]
            new2osmWays[newWay.attrib["id"]] = wayOsm.attrib["id"]
            #check if tags are equal
            if hasConflictingTags(newWay, wayOsm):
                # Make relation and make reference to other 
                minRelationId -= 1
                rel = ET.Element("relation", {'id':'%d' % minRelationId, 'visible':'true'} )
                rel.append(ET.Element("member", {'type':'way', 'role':'outer', 'ref':wayOsm.attrib["id"]} ))
                rel.append(ET.Element("tag", {'k':'type', 'v':'multipolygon'} ))
                for t in newWay.findall("tag"):
                    if (t.attrib["k"] != "source:date" and t.attrib["k"] != "source"):
                        rel.append(t)  
                osmImport.getroot().append(rel)
            else:
                oldTag = set()
                for t in wayOsm.findall("tag"):
                    oldTag.add(t.attrib["k"]+t.attrib["v"])
                newTags = set()
                for t in newWay.findall("tag"):
                    if (t.attrib["k"] != "source:date" and (t.attrib["k"]+t.attrib["v"]) not in oldTag):
                        newTags.add(t)           

                    
                if (len(newTags) > 0):
                    wayOsm.attrib["action"] = "modify"
                    for t in newTags:
                        wayOsm.append(t)
                if hashWay(wayOsm, nodesOsm) == reverseHashWay(newWay, nodes):
                    reverseWay(wayOsm)
                osmImport.getroot().append(wayOsm)
            try:
                osmImport.getroot().remove(newWay)
            except ValueError:
                print("There is a duplicate way with id: %s" %(wayOsm.attrib["id"]))
        else:
            shouldBeIncluded = False
            fromN50 = False
            for tag in wayOsm.findall("tag"):
                k = tag.attrib["k"]
                v = tag.attrib["v"]
                if (importWater and ((k == "natural" and v == "water") or (k == "waterway"))):
                    shouldBeIncluded = True
                elif (importAreal and ((k == "natural" and v != "water") or k=="landuse" or k=="leisure" or k=="aeroway" or k=="seamark:type")):
                    shouldBeIncluded = True
                elif (importWay and (k == "highway" or k=="barrier")):
                    shouldBeIncluded = True
                elif (importCoastline and (k == "natural" and v == "coastline")):
                    shouldBeIncluded = True
                if k=="source" and (v=="Kartverket N50" or v=="Kartverket" or v=="Statkart"):
                    fromN50 = True
            if shouldBeIncluded:
                if not fromN50:
                    wayOsm.append(ET.Element("tag", {'k':'FIXME', 'v':'Merge'} ))
                    wayOsm.attrib["action"] = "modify"
                osmImport.getroot().append(wayOsm)
                includedWays.add(wayOsm.attrib["id"])
                for nd in wayOsm.findall("nd"):
                    ref = nd.attrib["ref"]
                    if ref not in includedNodes:    
                        includedNodes.add(ref)
                        osmImport.getroot().append(nodesOsm[ref])
            
    new2osmRel = dict()
    for relOsm in oldOsm.findall("relation"):  
        try:
            hashStr = hashRelation(relOsm, waysOsm, nodesOsm)
        except KeyError:
            hashStr = None
        if hashStr in relationsHashed:
            rel = relationsHashed[hashRelation(relOsm, waysOsm, nodesOsm)]
            new2osmRel[rel.attrib["id"]] = relOsm.attrib["id"]
            try:
                osmImport.getroot().remove(rel)
            except KeyError:
                print("There is a duplicate relation with id: %s" %(relOsm.attrib["id"]))
        else:
            
            relFromN50 = False
            for mem in relOsm.findall("mem"):
                memRef = mem.attrib["ref"]
                if memRef in waysOsm:
                    for tag in waysOsm[memRef].findall("tag"):
                        k = tag.attrib["k"]
                        v = tag.attrib["v"]
                        if k=="source" and (v=="Kartverket N50" or v=="Kartverket" or v=="Statkart"):
                            relFromN50 = True
            shouldBeIncluded = False
            for tag in relOsm.findall("tag"):
                k = tag.attrib["k"]
                v = tag.attrib["v"]
                if (importWater and ((k == "natural" and v == "water") or (k == "waterway"))):
                    shouldBeIncluded = True
                elif (importAreal and ((k == "natural" and v != "water") or k=="landuse" or k=="leisure" or k=="aeroway")):
                    shouldBeIncluded = True
                elif (importCoastline and (k == "natural" and v == "coastline") ):
                    shouldBeIncluded = True
        
            if shouldBeIncluded:
                if not relFromN50:
                    relOsm.append(ET.Element("tag", {'k':'FIXME', 'v':'Merge'} ))
                    relOsm.attrib["action"] = "modify"
                osmImport.getroot().append(relOsm)
                for w in relOsm.findall("member"):
                    wRef = w.attrib["ref"]
                    if wRef not in includedWays and wRef in waysOsm:
                        wayOsm = waysOsm[wRef]
                        osmImport.getroot().append(wayOsm)
                        includedWays.add(wRef)
                        for nd in wayOsm.findall("nd"):
                            ref = nd.attrib["ref"]
                            if ref not in includedNodes:    
                                includedNodes.add(ref)
                                osmImport.getroot().append(nodesOsm[ref])
    
    for ref, way in ways.iteritems():
        if not ref in new2osmWays:
            for nd in way.findall("nd"):
                if nd.attrib["ref"] in new2osmNodes:
                    nd.attrib["ref"] = new2osmNodes[nd.attrib["ref"]]
     
    for rel in osmImport.getroot().findall("relation"):
        for member in rel.findall("member"):
            if member.attrib["type"] == "way":
                if member.attrib["ref"] in new2osmWays:
                    member.attrib["ref"] = new2osmWays[member.attrib["ref"]]
            elif member.attrib["type"] == "node":
                if member.attrib["ref"] in new2osmNodes:
                    member.attrib["ref"] = new2osmNodes[member.attrib["ref"]]
            else:
                raise Warning("Type of member in relation unknown (id %d)" % rel.attrib["id"])
    
    osmImport.getroot().attrib["upload"] = "True"
    osmImport.write(fileNameOut)

if __name__ == '__main__':
    fileName = None
    if (len(sys.argv) < 3):
        print("""The script requires at least two inputs:
Usage:
python replaceWithOsm.py inputFile outPutfile [--import:water] [--import:area] [--import:all]
            
            """)
        exit()
    else:
        fileName = sys.argv[1]
        fileNameOut = sys.argv[2]
        importWater = False
        importAreal = False
        importWay = False
        importCoastline = False
        if (len(sys.argv) == 4):
            imp = sys.argv[3]
            if imp== "--import:water":
                importWater = True
            elif imp == "--import:areal":
                importAreal = True
            elif imp == "--import:area":
                importAreal = True
            elif imp == "--import:way":
                importWay = True
            elif imp == "--import:coastline":
                importCoastline = True
            elif imp == "--import:all":
                importAreal = True
                importWater = True
                importWay = True
                importCoastline = True
            else:
                print("""The script requires at least two inputs:
Usage:
python replaceWithOsm.py inputFile outPutfile [--import:water] [--import:area] [--import:all]
                    
Unknown flag: %s """ % imp)
                exit()

        
        replaceWithOsm(fileName, fileNameOut,importAreal,importWater,importWay)
