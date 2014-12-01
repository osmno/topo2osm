from osgeo import gdal
import os

class DemFile:
    xMin = None
    dx = None
    yMax = None
    dy = None
    data = None
    dem = None
    def __init__(self,filename):
        self.dem = gdal.Open(filename)
        gt = self.dem.GetGeoTransform()
        self.xMin = gt[0]
        self.dx = gt[1]
        self.yMax = gt[3]
        self.dy = gt[5]
        
    def getElevation(self,x,y):
        if self.data is None:
            self.data = self.dem.ReadAsArray()
        i = (x-self.xMin)/self.dx
        j = (y-self.yMax)/self.dy
        di = i % 1
        dj = j % 1
        i = int(i)
        j = int(j)
        try:
            # Linear interpolation
            v1 = self.data[j][i]
            v2 = self.data[j][i+1]
            V1 = v1*(1-di)+v2*di
            v1 = self.data[j+1][i]
            v2 = self.data[j+1][i+1]
            V2 = v1*(1-di)+v2*di
            return V1*(1-dj)+V2*dj
        except IndexError:
            raise Exception("Out of range of loaded DEM file")

class Elevation:
    demFiles = []
    def __init__(self,DemFolder=r"./DEM"):
        files = os.listdir(DemFolder)
        i = 0;
        for f in files:
            i += 1
            if f.split(".")[-1] == "dem":
                dem = DemFile(os.path.join(DemFolder,f))
                k = 0
                for row in self.demFiles:
                    if row['xMin'] == dem.xMin:
                        j = 0
                        for col in row['dem']:
                            if col.yMax > dem.yMax:
                                row['dem'].insert(j,dem)
                                break
                            else:
                                j += 1
                        if j == len(row['dem']):
                            row['dem'].append(dem)
                        break
                    elif row['xMin'] < dem.xMin:
                        self.demFiles.insert(max(k,0),{'xMin':dem.xMin,'dem':[dem]})
                        break
                    k += 1
                if (k == len(self.demFiles)):
                    self.demFiles.append({'xMin':dem.xMin,'dem':[dem]})
        
        # Test
        #xMinOld = inf
        # for row in self.demFiles:
        #     assert xMinOld > row['xMin']
        #     xMinOld = row['xMin']
        #     yMaxOld = -inf
            #print('xMin: %d' % xMinOld)
        #     for d in row['dem']:
        #         assert d.yMax > yMaxOld
        #         yMaxOld = d.yMax
                #print('yMax: %d' % yMaxOld)
        print("Finished loading DEM files")
            
                
    def getElevation(self,x,y):
        for row in self.demFiles:
            if row['xMin'] <= x:
                for dem in row['dem']:
                    if dem.yMax >= y:
                        return dem.getElevation(x,y)
                        
if __name__ == '__main__':
    import unittest
    ele = Elevation()
    class TestSequenceFunctions(unittest.TestCase):
        def test_some_points(self):
            self.assertAlmostEqual(ele.getElevation(209930.508, 6970410.426),1598.,delta=1.5)
            self.assertAlmostEqual(ele.getElevation(211366.488, 6970090.438),1060.,delta=1.5)
            
    unittest.main()
