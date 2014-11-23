from mergeroads import findCropCandidate,distanceBetweenWays,nodes2nodeList
from lxml import etree
import unittest

class TestSequenceFunctions(unittest.TestCase):
    def test_distance_950m(self):
        test = etree.parse("testfiles/testParallel950m.osm")
        newWays = test.findall("way")
        newNodes = nodes2nodeList(test.findall("node"))
        candidate = newWays[1]
        newWay = newWays[0]
        nodesCandidate = candidate.findall('nd')
        cropStartCandidate, cropEndCandidate = findCropCandidate(nodesCandidate,newNodes,newWay,newNodes,candidate)
        mean, variance = distanceBetweenWays(newNodes,newWay,newNodes,nodesCandidate,cropStartCandidate,cropEndCandidate)
        self.assertEqual(950, mean)
        self.assertEqual(0, variance, "Var is wrong")

if __name__ == '__main__':
    unittest.main()