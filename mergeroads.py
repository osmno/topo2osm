from lxml import etree
from math import sin, cos, sqrt, atan2, radians

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
            wl = e['ways']
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

def latLonDistance(lon, lat,lon2, lat2):
    R = 6373000.

    lat1 = radians(lat)
    lon1 = radians(lon)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = (sin(dlat/2))**2 + cos(lat1) * cos(lat2) * (sin(dlon/2))**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def nearestNodeInWay(node,nodeListNewWay,wayCandidate,nodeListCandidate,minNode=0,maxNode=-1):
    node = nodeListNewWay[node.attrib['ref']]
    lat = float(node.attrib['lat'])
    lon = float(node.attrib['lon'])
    shortestDistance = 1e100
    iShortest = -1
    i = -1
    for n in wayCandidate.findall("nd"):
        i += 1
        if (i>= minNode) and (maxNode<0 or i <= maxNode ):
            n = nodeListCandidate[n.attrib['ref']]
            lat2 = float(n.attrib["lat"])
            lon2 = float(n.attrib["lon"])
            distance = latLonDistance(lon,lat,lon2,lat2)
            if distance < shortestDistance:
                shortestDistance = distance
                iShortest = i

    assert shortestDistance < 1e100
    return {'node':iShortest, 'distance':shortestDistance}

def nearestNodeInNewWay(node,nodeListCandidate,way,nodeListNewWay,minNode=0,minSegment=0,maxNode=-1,maxSegment=-1):
    node = nodeListCandidate[node.attrib['ref']]
    lat = float(node.attrib['lat'])
    lon = float(node.attrib['lon'])
    shortestDistance = 1e100
    nodeShortest = -1
    segmentShortest = -1
    segmentI = -1
    for segment in way['ways']:
        segmentI += 1
        nodeJ = -1
        if segmentI>=minSegment and (maxSegment <= 0 or segmentI <= maxSegment):
            for n in segment.findall("nd"):
                nodeJ += 1
                if nodeJ>=minNode and (maxNode < 0 or nodeJ <= maxNode):
                    n = nodeListNewWay[n.attrib['ref']]
                    lat2 = float(n.attrib["lat"])
                    lon2 = float(n.attrib["lon"])
                    distance = latLonDistance(lon,lat,lon2,lat2)
                    if distance < shortestDistance:
                        shortestDistance = distance
                        nodeShortest = nodeJ
                        segmentShortest = segmentI
    return {'segment':segmentShortest,'node':nodeShortest, 'distance':shortestDistance}

new = etree.parse("new.osm")
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
    smallestMean = 1e100
    smallestVar = 1e100
    for candidate in ways:
        nodesCandidate = candidate.findall('nd')
        n = nodesCandidate[0]
        # Find begining and end of road
        beginingCandidate2newWay = nearestNodeInNewWay(nodesCandidate[0],oldNodes,newWay,newNodes)
        endCandidate2newWay = nearestNodeInNewWay(nodesCandidate[-1],oldNodes,newWay,newNodes)
        beginingNewWay2Candidate =  nearestNodeInWay(newWay['ways'][0].findall('nd')[0],newNodes,candidate,oldNodes)
        endNewWay2Candidate =       nearestNodeInWay(newWay['ways'][-1].findall('nd')[-1],newNodes,candidate,oldNodes)
        # Check if candidate way should be reversed
        cropStartCandidate = 0
        cropEndCandidate = 0
        cropStartNewWay = {'node':0,'segment':0}
        cropEndNewWay = {'node':0,'segment':0}
        # Check which begining is closest to the other road
        if (beginingNewWay2Candidate['node']<endNewWay2Candidate['node']):
            if beginingNewWay2Candidate['distance']<beginingCandidate2newWay['distance']:
                cropStartNewWay = {'node':0,'segment':0}
                cropStartCandidate = beginingNewWay2Candidate['node']
            else:
                cropStartNewWay = {'node':beginingCandidate2newWay['node'],'segment':beginingCandidate2newWay['segment']}
                cropStartCandidate = 0
            if endNewWay2Candidate['distance']<endCandidate2newWay['distance']:
                cropEndCandidate = endNewWay2Candidate['node']
                cropEndNewWay = {'node':-1,'segment':-1}
            else:
                cropEndCandidate = -1
                cropEndNewWay = {'node':endCandidate2newWay['node'],'segment':endCandidate2newWay['segment']}
                        
        else:
            if beginingNewWay2Candidate['distance']<endCandidate2newWay['distance']:
                cropStartNewWay = {'node':0,'segment':0}
                cropEndCandidate = beginingNewWay2Candidate['node']
            else:
                cropStartNewWay = {'node':endCandidate2newWay['node'],'segment':endCandidate2newWay['segment']}
                cropEndCandidate = -1
            if endNewWay2Candidate['distance']<beginingCandidate2newWay['distance']:
                cropStartCandidate = endNewWay2Candidate['node']
                cropEndNewWay = {'node':-1,'segment':-1}
            else:
                cropStartCandidate = 0
                cropEndNewWay = {'node':beginingCandidate2newWay['node'],'segment':beginingCandidate2newWay['segment']}
        
        # Find length to nodes in way
        i = -1
        distance = []
        for node in nodesCandidate:
            i += 1
            if (i >= cropStartCandidate) and (cropEndCandidate < 0 or i<=cropEndCandidate):
                out = nearestNodeInNewWay(node,oldNodes,newWay,newNodes,cropStartNewWay['node'],cropStartNewWay['segment'],cropEndNewWay['node'],cropEndNewWay['segment'])
                distance.append(out['distance'])
        #print distance
        # Find mean and variance of distance between roads
        mean = 0.
        for d in distance:
            mean += d
        mean /= float(len(distance))
        variance = 0.
        for d in distance:
            variance += (d-mean)**2
        variance /= float(len(distance))
        variance = variance**.5
        smallestMean = min(mean,smallestMean)
        smallestVar = min(variance,smallestVar)
        if mean < 50 and variance < 50**2:
            # newWay is in oldWays if mean<tolMean and var<tolVar
            for way in newWay['ways']:
                new.getroot().remove(way)
            break
        else:
            for way in newWay['ways']:
                way.attrib['mean']=str(smallestMean)
                way.attrib['var'] = str(smallestVar)

## remove delted nodes
# list all nodes
ref = set()
for i in newNodes:
    ref.add(int(i))
for way in new.getroot().findall('way'):
    for n in way.findall('nd'):
        if int(n.attrib['ref']) in ref:
            ref.remove(int(n.attrib['ref']))
for r in ref:
    new.getroot().remove(newNodes[str(r)])


new.write("testParsed.osm")

