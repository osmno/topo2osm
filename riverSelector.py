from lxml import etree
from math import sin, pi,fabs, sqrt
import geographiclib.geodesic as gg
import sys
import cProfile
from numpy import arctan2



def nodes2nodeList(nodes):
    l = {}
    for n in nodes:
        l[n.attrib['id']] = n
    return l

# Itterates thourgh all ways in possibleWays and check if the bBox overlaps with the bbox of way.
def findCloseOverlappingRoads(way,possibleWays):
    l = []
    bBoxN = way.bBoxN
    bBoxS = way.bBoxS
    bBoxW = way.bBoxW
    bBoxE = way.bBoxE
    for w in possibleWays:
        if float(w.bBoxS)<bBoxN and float(w.bBoxE)>bBoxW and float(w.bBoxW)<bBoxE and float(w.bBoxN)>bBoxS:
            l.append(w)
    return l


# Calculates the distance between two points
def latLonDistance(lon, lat,lon2, lat2):
    if not hasattr(latLonDistance, "dxdlon"):
        # Linearization of distance
        dlat = .001
        out = gg.Geodesic.WGS84.Inverse(lat,lon,lat+dlat,lon)
        latLonDistance.dydlat = out["s12"]/dlat
        dlon = .001
        out = gg.Geodesic.WGS84.Inverse(lat,lon,lat,lon+dlon)
        latLonDistance.dxdlon = out["s12"]/dlon
    dx = (lon2-lon)*latLonDistance.dxdlon
    dy = (lat2-lat)*latLonDistance.dydlat
    return sqrt(dx*dx+dy*dy)

def latLonBearing(lon1, lat1, lon2, lat2):
    if not hasattr(latLonBearing, "dxdlon"):
        # Linearization of distance
        dlat = .001
        out = gg.Geodesic.WGS84.Inverse(lat1,lon1,lat1+dlat,lon1)
        latLonBearing.dydlat = out["s12"]/dlat
        dlon = .001
        out = gg.Geodesic.WGS84.Inverse(lat1,lon1,lat1,lon1+dlon)
        latLonBearing.dxdlon = out["s12"]/dlon
    dx = (lon2-lon1)*latLonBearing.dxdlon
    dy = (lat2-lat1)*latLonBearing.dydlat
    return arctan2(dx,dy)

# Calculate the distance to the closest node in way from node
def nearestNodeInWay(node,way,nodeListWay,minNode=0,maxNode=-1):
#   node = nodeListNewWay[node.attrib['ref']]
    lat = float(node.attrib['lat'])
    lon = float(node.attrib['lon'])
    shortestDistance = 1e100
    bearingToShortest = 0
    iShortest = -1
    i = -1
    for n in way.findall("nd"):
        i += 1
        if (i>= minNode) and (maxNode<0 or i <= maxNode ):
            n = nodeListWay[n.attrib['ref']]
            lat2 = float(n.attrib["lat"])
            lon2 = float(n.attrib["lon"])
            distance = latLonDistance(lon,lat,lon2,lat2)
            if distance < shortestDistance:
                shortestDistance = distance
                bearingToShortest = latLonBearing(lon,lat,lon2,lat2)
                iShortest = i

    assert shortestDistance < 1e100
    return {'node':iShortest, 'distance':shortestDistance, 'bearing':bearingToShortest}

# Calculate the mean and variance of the absolute distance between newWay and nodesCandidate
# oldNodes - list of nodes elements 
def distanceBetweenWays(way1, nodes1, way2, nodes2,cropStartWay1,cropEndWay1):          
    # Find length to nodes in way
    i = -1
    distance = []
    nodesWay1 = way1.findall("nd")
    
    if len(nodesWay1) < 2 or (cropStartWay1 >= cropEndWay1 and cropEndWay1 > 0) or (cropStartWay1 is len(nodesWay1) -1) :
        print('Ignoring way with one node. CropStart: %d CropEnd: %d Length: %d' % (cropStartWay1,cropEndWay1, len(nodesWay1)))
        return (1e100,1e100)
    else:
        print('Not ignoring way with one node. CropStart: %d CropEnd: %d Length: %d' % (cropStartWay1,cropEndWay1, len(nodesWay1)))
    n = nodes1[nodesWay1[1].attrib['ref']]
    prevLat = float(n.attrib['lat'])
    prevLon = float(n.attrib['lon'])
    for node in nodesWay1:
        i += 1
        n = nodes1[node.attrib["ref"]]
        lat = float(n.attrib['lat'])
        lon = float(n.attrib['lon'])
        if (i >= cropStartWay1) and (cropEndWay1 < 0 or i<=cropEndWay1):
            out = nearestNodeInWay(nodes1[node.attrib["ref"]],way2,nodes2)
            absDistance = fabs(out['distance'])
            # Find angle between direction to previous and nearest node
            bearingToNearestNode = out['bearing']
            bearingToPreviousNode = latLonBearing(lon, lat, prevLon, prevLat)
            if i == 0:
                bearingToPreviousNode -= pi
            d = sin(bearingToNearestNode-bearingToPreviousNode)*absDistance
            distance.append(d)
        prevLat = lat
        prevLon = lon
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
    return (mean,variance)

# Find the closest nodes to the begining and end of newWay in nodesCandidate
def findCropCandidate(way1,nodes1,way2,nodes2):
    # Find begining and end of road
    beginingWay1ToWay2 =  nearestNodeInWay(nodes1[way1.findall('nd')[0].attrib["ref"]],way2,nodes2)
    endWay1ToWay2 =       nearestNodeInWay(nodes1[way1.findall('nd')[-1].attrib["ref"]],way2,nodes2)
    beginingWay2ToWay1 =  nearestNodeInWay(nodes2[way2.findall('nd')[0].attrib["ref"]],way1,nodes1)
    endWay2ToWay1 =        nearestNodeInWay(nodes2[way2.findall('nd')[-1].attrib["ref"]],way1,nodes1)
    ## Check if candidate way should be reversed
    cropStartWay1 = 0
    cropEndWay1 = 0
    # Check which begining is closest to the other road
    if (beginingWay2ToWay1['node']<endWay2ToWay1['node']):
        if beginingWay2ToWay1['distance']<beginingWay1ToWay2['distance']:
            cropStartWay1 = beginingWay2ToWay1['node']
        else:
            cropStartWay1 = 0
        if endWay2ToWay1['distance']<endWay1ToWay2['distance']:
            cropEndWay1 = endWay2ToWay1['node']
        else:
            cropEndWay1 = -1
                    
    else:
        # reverse direction
        if beginingWay2ToWay1['distance']<endWay1ToWay2['distance']:
            cropEndWay1 = beginingWay2ToWay1['node']
        else:
            cropEndWay1 = -1
        if endWay2ToWay1['distance']<beginingWay1ToWay2['distance']:
            cropStartWay1 = endWay2ToWay1['node']
        else:
            cropStartWay1 = 0  
    assert (cropStartWay1 < cropEndWay1) or (cropEndWay1 is -1), "crop start %d crop end %d" % (cropStartWay1,cropEndWay1)
    return cropStartWay1, cropEndWay1

## remove delted nodes
def removeNodesNotInWay(newOsm, newNodes):
    # list all nodes
    ref = set()
    for i in newNodes:
        ref.add(int(i))
    for way in newOsm.getroot().findall('way'):
        for n in way.findall('nd'):
            if int(n.attrib['ref']) in ref:
                ref.remove(int(n.attrib['ref']))
    for r in ref:
        newOsm.getroot().remove(newNodes[str(r)])

# Class for wrapping and combining ways
class wayWrapper:
    ways = []
    bBoxN = -90.
    bBoxE = -180.
    bBoxS = 90.
    bBoxW = 180.        
    def __init__(self,way,nodes):
        self.ways = [way]
        for nd in way.findall("nd"):
            n = nodes[nd.attrib['ref']]
            lat = float(n.attrib["lat"])
            lon = float(n.attrib["lon"])
            self.bBoxN = max(self.bBoxN,lat)
            self.bBoxS = min(self.bBoxS,lat)
            self.bBoxW = min(self.bBoxW,lon)
            self.bBoxE = max(self.bBoxE,lon)
    def addWay(self,way):
        for i in range(len(way.ways)):
            self.ways.append(way.ways[i])
        self.boxN = max(self.bBoxN,way.bBoxN)
        self.boxE = max(self.bBoxE,way.bBoxE)
        self.boxW = min(self.bBoxW,way.bBoxW)
        self.boxS = min(self.bBoxS,way.bBoxS)
        
    def findall(self,searchString):
        res = self.ways[0].findall(searchString)
        for i in range(1,len(self.ways)):
            res += self.ways[i].findall(searchString)
        return res
    
def main():
    if len(sys.argv) is not 4:
        print """The script requires three inputs, %d was given
    Usage: python mergeroads new.osm old.osm output.osm
    - new.osm  Data to be merged into old.osm
    - old.osm Existing data, new ways should not be close to ways in old.osm
    - output.osm Output file
    Input was: %s """  % (len(sys.argv)-1, str(sys.argv))
        exit()
        
    new = etree.parse(sys.argv[1])
    old = etree.parse(sys.argv[2])
    
    newWays = new.findall("way")
    newNodes = nodes2nodeList(new.findall("node"))
    oldWays = old.findall("way")
    oldNodes = nodes2nodeList(old.findall("node"))
    
    for i in range(len(newWays)):
        newWays[i] = wayWrapper(newWays[i],newNodes)
    
    for i in range(len(oldWays)):
        oldWays[i] = wayWrapper(oldWays[i],oldNodes)
    
    for _,newWay in newWays.iteritems():
        # Find roads with overlapping bBox (Union)
        closeWays = findCloseOverlappingRoads(newWay,oldWays)
        for wayCandidate in closeWays:
            cropStartCandidate, cropEndCandidate = findCropCandidate(wayCandidate,oldNodes,newWay,newNodes)
            mean, variance = distanceBetweenWays(newWay,newNodes,wayCandidate,oldNodes,cropStartCandidate,cropEndCandidate)
            if abs(mean) < 20 and variance < 5**2:
                # newWay is in oldWays if mean<tolMean and var<tolVar
                for way in newWay.ways:
                    new.getroot().remove(way)
                break
    
    
    
    
    removeNodesNotInWay(new,newNodes)
    new.write(sys.argv[3])

if __name__ == "__main__":
    main()
    
    cProfile.run('main()', 'restats',sort="cumtime")
    import pstats
    p = pstats.Stats('restats')
    p.dump_stats("profile.txt")
    p.sort_stats("cumtime").print_callers()