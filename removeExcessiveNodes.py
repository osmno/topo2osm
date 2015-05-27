import sys
from nodes2nodeList import nodes2nodeList
from offsetDistance import openOsm,getOffsetDistance
from math import fabs

def removeExcessiveNodes(fileName, fileNameOut,cutoffDistance):
    
    f = openOsm(fileName)
    nodes = nodes2nodeList(f.findall("node"))
    ways = f.findall("way")
    removeNodes = {}
    for w in ways:
        nd = w.findall("nd")
        for i in range(2,len(nd)):
            tripels = [nd[i-2], nd[i-1],nd[i]] 
            if (fabs(getOffsetDistance(tripels, nodes)) < cutoffDistance):
                removeNodes[nd[i-1].attrib["ref"]] = w.attrib["id"]
                nd[i-1] = nd[i-2]
    for w in ways:
        for nd in w.findall("nd"):
            if nd.attrib["ref"] in removeNodes:
                if removeNodes[nd.attrib["ref"]] != w.attrib["id"]:
                    removeNodes.pop(nd.attrib["ref"], None)
    
    for w in ways:
        for nd in w.findall("nd"):
            if nd.attrib["ref"] in removeNodes:
                w.remove(nd)
                f.getroot().remove(nodes[nd.attrib["ref"]])
    
    f.write(fileNameOut)

    
    
if __name__ == '__main__':
    fileName = None
    if (len(sys.argv) < 3):
        print("""The script requires at least two inputs:
Usage:
python removeExcessiveNodes.py inputFile outPutfile
            
            """)
        exit()
    else:
        fileName = sys.argv[1]
        fileNameOut = sys.argv[2]
        cutoffDistance = float(sys.argv[3])
        removeExcessiveNodes(fileName, fileNameOut,cutoffDistance)