'''
Created on Dec 23, 2015

@author: torsteinibo
'''
import sys
from replaceWithOsm import openOsm, nodes2nodeList
from lxml import etree as ET
from copy import deepcopy


def copyNodes(inOsm, extractOsm):
    # Copy nodes in overlapping ways
    nodes = nodes2nodeList(inOsm.getroot().findall("node"))
    usedNodes = set()
    for n in extractOsm.xpath("way/nd"):
        usedNodes.add(n.attrib['ref'])
    
    for n in usedNodes:
        try:
            extractOsm.getroot().append(deepcopy(nodes[n]))
        except KeyError:
            if int(n)<0:
                print("Missing node %s" % n)
    return usedNodes

def removeUnusedNodes(osm, checkNodes):
    for nd in osm.xpath("way/nd"):
        if nd.attrib["ref"] in checkNodes:
            checkNodes.remove(nd.attrib["ref"])
    nodes = nodes2nodeList(inOsm.getroot().findall("node"))
    for n in checkNodes:
        osm.getroot().remove(nodes[n])
        

def extractOverlapping(inOsm,outOsmFileName):
    extractOsm = ET.ElementTree(ET.fromstring("""<osm version='0.6' upload='false' generator='JOSM'></osm>"""))
    extractOsmRel = ET.ElementTree(ET.fromstring("""<osm version='0.6' upload='false' generator='JOSM'></osm>"""))
    ways = nodes2nodeList(inOsm.getroot().findall("way"))
    
    # Split into osm ways and new ways
    waysOsm = {}
    waysImport = {}
    for (idx,w) in ways.iteritems():
        if int(idx) < 0:
            waysImport[idx] = w
        else:
            waysOsm[idx] = w
    
    # Extract overlapping new ways
    for (idx,w) in waysImport.iteritems():
        if (findOverlappingWay(3, w, waysOsm) is not None):
            extractOsm.getroot().append(w)

            
    # Move ways to relation file 
    extractWays = set()
    for w in extractOsm.getroot().findall("way"):
        extractWays.add(w.attrib['id'])
    
    for rel in inOsm.getroot().findall("relation"):
        isIn = False
        for mem in rel.findall('member'):
            if mem.attrib['ref'] in extractWays:
                isIn = True
                break
            elif int(mem.attrib['ref']) > 0 and int(rel.attrib["id"]) < 0: 
                isIn = True
                break
        if isIn:
            if int(rel.attrib["id"]) > 0:
                for mem in rel.findall('member'):
                    ref = mem.attrib['ref']
                    if ref in extractWays:
                        inOsm.getroot().append(waysImport[ref])
            else:
                for mem in rel.findall('member'):
                    ref = mem.attrib['ref']
                    if int(ref)< 0:
                        extractOsmRel.getroot().append(waysImport[ref])
                extractOsmRel.getroot().append(rel)

    mems = set()
    for rel in inOsm.getroot().findall("relation"):
        for mem in rel.findall('member'):
            mems.add(mem.attrib['ref'])
            
    for w in extractOsm.getroot().findall("way"):
        if w.attrib['id'] in mems:
            inOsm.getroot().append(deepcopy(w))
    
    for w in extractOsmRel.getroot().findall("way"):
        if w.attrib['id'] in mems:
            inOsm.getroot().append(deepcopy(w))
    
            
    copiedNodes =  copyNodes(inOsm, extractOsm)
    copiedNodes = copiedNodes | copyNodes(inOsm, extractOsmRel) 
    removeUnusedNodes(inOsm, copiedNodes)
    
        
        
    inOsm.write("%s_merge.osm" % outOsmFileName )
    extractOsm.write("%s_extract_way.osm" % outOsmFileName)
    extractOsmRel.write("%s_extract_rel.osm" % outOsmFileName)
    

    

def findOverlappingWay(overLapping,way,waysOsm):
    nodes = set()
    for nd in way.findall("nd"):
        nodes.add(nd.attrib["ref"])
    overLapping = min(len(nodes),overLapping)
    
    for _,w in waysOsm.iteritems():
        match = 0
        nodesCandidate = w.findall("nd")
        for nd in nodesCandidate:
            if nd.attrib["ref"] in nodes:
                match += 1
                if (match >= overLapping):
                    return w
    return None



if __name__ == '__main__':
    fileName = None
    if (len(sys.argv) < 3):
        print("""The script requires at least two inputs:
Usage:
python extractOverlapping.py inputFile outputFileName
            
            """)
        exit()
    else:
        fileName = sys.argv[1]
        fileNameOut = sys.argv[2]
        inOsm = openOsm(fileName)
        extractOverlapping(inOsm, fileNameOut)