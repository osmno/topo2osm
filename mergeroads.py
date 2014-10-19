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
    bBoxN = way["bBoxN"]
    bBoxS = way["bBoxS"]
    bBoxW = way["bBoxW"]
    bBoxE = way["bBoxE"]
    for w in possibleWays:
        if float(w.attrib["bBoxS"])<bBoxN and float(w.attrib["bBoxE"])>bBoxW and float(w.attrib["bBoxW"])<bBoxE and float(w.attrib["bBoxN"])>bBoxS:
            l.append(w)
    return l

def combineRoads(ways):
    l = {}
    wl = []
    for w in ways:
        tags = w.findall("tag")
        ref = 1
        highway = ''
        for t in tags:
            if t.attrib['k'] == "ref":
                ref = int(t.attrib['v'])
            elif t.attrib['k'] == 'highway':
                highway = t.attrib['v']
        k = '%s%d' % (highway,ref)
        if k in l:
            e = l[k]
            bBoxN = max(e['bBoxN'],float(w.attrib["bBoxN"]))
            bBoxS = min(e['bBoxS'],float(w.attrib["bBoxS"]))
            bBoxW = min(e['bBoxW'],float(w.attrib["bBoxW"]))
            bBoxE = max(e['bBoxE'],float(w.attrib["bBoxE"]))
            wl.append(w)
            l[k] = {'ways': wl, 'bBoxN':bBoxN,'bBoxS':bBoxS,'bBoxW':bBoxW,'bBoxE':bBoxE}
        else:
            bBoxN = float(w.attrib["bBoxN"])
            bBoxS = float(w.attrib["bBoxS"])
            bBoxW = float(w.attrib["bBoxW"])
            bBoxE = float(w.attrib["bBoxE"])
            wl = [w]
            l[k] = {'ways': wl, 'bBoxN':bBoxN,'bBoxS':bBoxS,'bBoxW':bBoxW,'bBoxE':bBoxE}


    return l

new = etree.parse("out.osm")
old = etree.parse("old.osm")

newWays = new.findall("way")
newNodes = nodes2nodeList(new.findall("node"))
oldWays = old.findall("way")
oldNodes = nodes2nodeList(old.findall("node"))

setBBox(newWays,newNodes)
setBBox(oldWays,oldNodes)
newWays = combineRoads(newWays)
for k,newWay in newWays.iteritems():
    # Find roads with overlapping bBox (Union)
    ways = findCloseOverlappingRoads(newWay,oldWays)
    # TODO Find begining and end of road
    # TODO Find length to nodes in way
    # TODO Find mean and variance of distance between roads
    # TODO newWay is in oldWays if mean<tolMean and var<tolVar
    print len(ways)

new.write("outParsed.osm")

