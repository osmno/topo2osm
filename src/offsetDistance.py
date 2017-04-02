'''
Created on Feb 2, 2015

@author: torsteinibo
'''
import unittest

from lxml import etree as ET
from nodes2nodeList import nodes2nodeList
import geographiclib.geodesic as gg
from math import sqrt, fabs

class latLonDistance:
    dxdlon = None
    dydlon = None
    
    def latLonDistanceNodes(self,node1,node2):
        lon1 = float(node1.attrib["lon"])
        lat1 = float(node1.attrib["lat"])
        lon2 = float(node2.attrib["lon"])
        lat2 = float(node2.attrib["lat"])
        return self.latLonDistance(lon1, lat1, lon2, lat2)
    
    # Calculates the distance between two points
    def latLonDistance(self,lon, lat,lon2, lat2):
        if self.dxdlon is None:
            # Linearization of distance
            dlat = .001
            out = gg.Geodesic.WGS84.Inverse(lat,lon,lat+dlat,lon)
            self.dydlat = out["s12"]/dlat
            dlon = .001
            out = gg.Geodesic.WGS84.Inverse(lat,lon,lat,lon+dlon)
            self.dxdlon = out["s12"]/dlon
        dx = (lon2-lon)*self.dxdlon
        dy = (lat2-lat)*self.dydlat
        dl = sqrt(dx*dx+dy*dy)
        return (dl,dx,dy)

distCalc = latLonDistance()
def getOffsetDistance(trippleNodes,nodeList):
    nd0 = nodeList[trippleNodes[0].attrib["ref"]]
    nd1 = nodeList[trippleNodes[1].attrib["ref"]]
    nd2 = nodeList[trippleNodes[2].attrib["ref"]]
    (dl,dx,dy) = distCalc.latLonDistanceNodes(nd0,nd2)
    if dl == 0:
        return 0.
    else:
        dx /= dl
        dy /= dl
        co = dx
        si = dy
        (_,dx,dy) = distCalc.latLonDistanceNodes(nd0,nd1)
        
        
        return dx*si-dy*co

def openOsm(fileName):
    return ET.parse(fileName)

class Test(unittest.TestCase):


    def testOffsetDistance(self):
        f = openOsm('testfiles/testVerticalDistance.osm')
        nodes = nodes2nodeList(f.findall("node"))
        way = f.findall("way")[0]
        nd = way.findall("nd")

        self.assertAlmostEqual(fabs(getOffsetDistance(nd, nodes)),596.21954504354)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testOffsetDistance']
    unittest.main()