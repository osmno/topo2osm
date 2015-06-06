'''
Created on Nov 29, 2014

@author: torsteinibo
'''

from lxml import etree
from nodes2nodeList import nodes2nodeList
import sys
import os

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
            
class relationWrapper:
    outerWays = None
    element = None  
    findall = None
    remove = None
    append = None
    nMem = None
    
    def __init__(self,element):
        self.element = element
        self.attrib = element.attrib
        self.findall = element.findall
        self.remove = element.remove
        self.append = element.append
        self.outerWays = set()
        members = element.findall("member")
        self.nMem = len(members)
        for way in members:
            if way.attrib["type"] == "way" and way.attrib["role"] == "outer":
                #self.includeArea(ways[way.attrib["ref"]])
                self.outerWays.add(way.attrib["ref"])
                
    
    def includeArea(self,element):
        for w in element.outerWays:
            self.outerWays.add(w)
#         self.bBoxN = max(self.bBoxN,element.bBoxN)
#         self.bBoxN = max(self.bBoxE,element.bBoxE)
#         self.bBoxN = min(self.bBoxW,element.bBoxW)
#         self.bBoxN = min(self.bBoxS,element.bBoxS)
#     def overlaps(self,element):
#         return (self.bBoxW < element.bBoxE or self.bBoxE > element.bBoxW) \
#             and (self.bBoxS < element.bBoxN or self.boxN > element.bBoxS)

def simplifyRelations(osmFile,relations):
    categories = []
    for rel in relations:
        if int(rel.attrib["id"])<0:
            isMultipolygon = False
            tags = dict()
            for tag in rel.findall("tag"):
                if "k" in tag.attrib:
                    if tag.attrib["k"] =="type" and tag.attrib["v"] == "multipolygon":
                        isMultipolygon = True
                    elif tag.attrib["k"] == "source:date":
                        pass
                    else:
                        tags[tag.attrib["k"]] = tag.attrib["v"]
    
            if isMultipolygon:
                # Find category
                isEqual = False
                for cat in categories:
                    catTags = cat["tags"]
                    if len(catTags) == len(tags):
                        isEqual = True
                        for key, value in tags.iteritems():
                            if not ( (key in catTags) and (catTags[key] == value)):
                                isEqual = False
                                break
                            
                        if isEqual:
                            cat["relation"].append(rel)
                            break
                if not isEqual:
                    categories.append({"tags":tags,"relation":[rel]})
    
    for cat in categories:
        ignoreRel = set()
        multipolygons = cat["relation"]
        hasMerged = True
        while hasMerged:
            hasMerged = False
            i = -1
            for rel in multipolygons:
                i += 1
                if (not i in ignoreRel) and (int(rel.attrib["id"])<0) and len(rel.findall("member"))<20:
                    for j in range(0,len(multipolygons)):            
                        if i != j and (not j in ignoreRel):
                            cand = multipolygons[j]
                            cNMem = len(cand.findall("member"))
                            rNMem = len(rel.findall("member"))
                            if int(cand.attrib["id"])<0 and (rNMem + cNMem<100 or rNMem<15):
                                equalOuter = rel.outerWays & cand.outerWays
                                if len(equalOuter)>0:
                                    #hasMerged = True
                                    for mem in rel.findall("member"):
                                        if (mem.attrib["ref"] in equalOuter):
                                            rel.remove(mem)
                                    for cmem in cand.findall("member"):
                                        if not (cmem.attrib["ref"] in equalOuter):
                                            rel.append(cmem)
                                    try:
                                        osmFile.getroot().remove(cand.element)
                                    except ValueError:
                                        print("Could not remove %s" % cand.element.attrib["id"])
                                    ignoreRel.add(j)
                                    rel.includeArea(cand)
                            
            
    
def removeRel(fileName,fileNameOut):
    osmFile = etree.parse(fileName)
    
    relations = osmFile.getroot().findall("relation")
    ways = nodes2nodeList(osmFile.getroot().findall("way"))
    nodes = nodes2nodeList(osmFile.getroot().findall("node"))
    for rel in relations:
        keep = False
        for tag in rel.findall("tag"):
            if "k" in tag.attrib and not (tag.attrib["k"] == "source:date" or tag.attrib["k"] =="type" or tag.attrib["k"] =="ele") :
                keep = True
                break
        if keep:
            members = rel.findall("member")
            if len(members) == 1 and members[0].attrib["ref"] < 0:
                member = members[0]
                if (member.attrib["type"] == "way"):
                    member = ways[member.attrib["ref"]]
                elif (member.attrib["type"] == "node"):
                    member = nodes[member.attrib["ref"]]
                else:
                    raise ValueError("Unknown type of only member in relation %s" % rel.attrib["id"])
                for tag in rel.findall("tag"):
                    if "k" in tag.attrib and not (tag.attrib["k"] =="type") :
                        member.append(tag)
                osmFile.getroot().remove(rel)
        else:
            osmFile.getroot().remove(rel)
    
    wrappedRelations = []
    for rel in osmFile.getroot().findall("relation"):
        wrappedRelations.append(relationWrapper(rel))
    
    simplifyRelations(osmFile,wrappedRelations)
    
    memberWays = set()
    for rel in osmFile.getroot().findall("relation"):
        for member in rel.findall("member"):
            memberWays.add(member.attrib["ref"])
    
    keepNodes = set()
    for way in osmFile.getroot().findall("way"):
        keep = True
        if not way.attrib["id"] in memberWays:  
            keep = False
            for tag in way.findall("tag"):
                if "k" in tag.attrib and not (tag.attrib["k"] == "source:date" or tag.attrib["k"] =="type" or tag.attrib["k"] =="ele") :
                    keep = True
                    break
            if not keep:
                osmFile.getroot().remove(way)
        if keep:
            for nd in way.findall("nd"):
                keepNodes.add(int(nd.attrib["ref"]))
    
    for nd in osmFile.getroot().findall("node"):
        if not int(nd.attrib["id"]) in keepNodes:
            osmFile.getroot().remove(nd)
            
    
    
    osmFile.write(fileNameOut)


if __name__ == '__main__':
    fileName = None
    if (len(sys.argv) == 2):
        files = os.listdir(sys.argv[1])
        for f in files:
            if f.split(".")[-1] == "osm":
                print("processing %s" % f)
                fileName = os.path.join(sys.argv[1],f)
                removeRel(fileName,fileName)
                
        
    elif (len(sys.argv) != 3):
        print("""The script requires two inputs:
Usage:
python riverTurner.py inputFile outPutfile
            
            """)
        exit()
    else:
        fileName = sys.argv[1]
        fileNameOut = sys.argv[2]
        removeRel(fileName, fileNameOut)
