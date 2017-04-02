from mergeroads import findCropCandidate,distanceBetweenWays,nodes2nodeList,latLonDistance,latLonBearing
from lxml import etree
from math import pi, fabs
import unittest

class TestSequenceFunctions(unittest.TestCase):
    def test_distance_950m(self):
        test = etree.parse("testfiles/testParallel950m.osm")
        newWays = test.findall("way")
        newNodes = nodes2nodeList(test.findall("node"))
        wayCandidate = newWays[1]
        newWay = newWays[0]
        cropStartCandidate, cropEndCandidate = findCropCandidate(wayCandidate,newNodes,newWay,newNodes)
        mean, variance = distanceBetweenWays(newWay,newNodes,wayCandidate,newNodes,cropStartCandidate,cropEndCandidate) 
        self.assertAlmostEqual(950, fabs(mean),delta=2)
        self.assertAlmostEqual(0, variance, delta=2)
        
    def test_distance_between_nodes(self):
        
        test = etree.parse("testfiles/twoNodes640m140deg.osm")
        nodes = test.findall("node")
        
        lat1 = float(nodes[0].attrib["lat"])
        lat2 = float(nodes[1].attrib["lat"])
        lon1 = float(nodes[0].attrib["lon"])
        lon2 = float(nodes[1].attrib["lon"])
        
        self.assertAlmostEqual(640, latLonDistance(lon1, lat1, lon2, lat2),delta=2)
        self.assertAlmostEqual(140-180, latLonBearing(lon1, lat1, lon2, lat2)*180/pi,delta=.1) 
        

if __name__ == '__main__':
    unittest.main()