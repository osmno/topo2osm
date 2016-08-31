'''
Created on Nov 29, 2014

@author: torsteinibo
'''

from lxml import etree
import sys
import os


    
def removeRel(fileName,fileNameOut):
    osmFile = etree.parse(fileName)
    
    relations = osmFile.getroot().findall("relation")
    ways = osmFile.getroot().findall("way")
    nodes = osmFile.getroot().findall("node")
    for element in relations:
        if int(element.attrib["id"])>0:
            osmFile.getroot().remove(element)
            
    for element in ways:
        if int(element.attrib["id"])>0:
            osmFile.getroot().remove(element)
            
    for element in nodes:
        if int(element.attrib["id"])>0:
            osmFile.getroot().remove(element)
              
    
    
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
