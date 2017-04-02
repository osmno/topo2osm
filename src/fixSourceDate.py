'''
Created on Dec 30, 2015

@author: torsteinibo
'''

from lxml import etree as ET
import re

re.compile("\d{8}")

osm =  ET.parse("export.osm")
for n in osm.xpath("*/tag[@k='source:date']"):
    v = n.attrib["v"]
    if len(v) == 8 and int(v) > 19000000 and int(v) < 21000000:
            v = "%s-%s-%s" % (v[0:4],v[4:6],v[6:8])
            n.attrib["v"] = v
            p = n.xpath("..")[0]
            p.attrib["action"] = "modify"
osm.write("exportFix.osm")
        