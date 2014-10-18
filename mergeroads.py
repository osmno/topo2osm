from lxml import etree

def nodes2nodeList(nodes):
    l = {}
    for n in nodes:
        l[n.attrib['id']] = n
    return l

def setBBox(ways,nodes):
    for way in ways:
        bBoxE=-180.;
        bBoxW=180.;
        bBoxN=-90.;
        bBoxS=90.;
        for nd in way.findall("nd"):
            n = nodes[nd.attrib['ref']]
            lat = float(n.attrib["lat"])
            lon = float(n.attrib["lon"])
            if lat>bBoxN:
                bBoxN = lat
            if lat<bBoxS:
                bBoxS = lat
            if lon<bBoxW:
                bBoxW = lon
            if lon>bBoxE:
                bBoxE = lon
        way.set("bBoxE",str(bBoxE))
        way.set("bBoxW",str(bBoxW))
        way.set("bBoxN",str(bBoxN))
        way.set("bBoxS",str(bBoxS))

def findCloseOverlappingRoads(way,possibleWays):
    l = []
    bBoxN = float(way.attrib["bBoxN"])
    bBoxS = float(way.attrib["bBoxS"])
    bBoxW = float(way.attrib["bBoxW"])
    bBoxE = float(way.attrib["bBoxE"])
    for w in possibleWays:
        if float(w.attrib["bBoxS"])<bBoxN and float(w.attrib["bBoxE"])>bBoxW and float(w.attrib["bBoxW"])<bBoxE and float(w.attrib["bBoxN"])>bBoxS:
            l.append(w)
    return l


new = etree.parse("out.osm")
old = etree.parse("old.osm")

newWays = new.findall("way")
newNodes = nodes2nodeList(new.findall("node"))
oldWays = old.findall("way")
oldNodes = nodes2nodeList(old.findall("node"))

#TODO sla sammen veier
setBBox(newWays,newNodes)
setBBox(oldWays,oldNodes)

ways = findCloseOverlappingRoads(newWays[0],oldWays)
for w in ways:
    print w.attrib

new.write("outParsed.osm")

