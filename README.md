# kartverket2osm
Converts N50 map data downloaded from Kartverket (SOSI format) to the OpenStreetMap format (.osm). This is a forked version of kartverket2osm originally made by [tibnor](https://github.com/tibnor), and adds several new OSM area types and has support for Karverket's updated file format.

This README describes the Kartverket-to-OSM conversion scripts. If you've downloaded a zip archive with generated OSM files, you only need to use the `replaceWithOsm.py` script, which is described in the section "Oppsett" on the OSM wiki page [Topography import for Norway](https://wiki.openstreetmap.org/wiki/Import/Catalogue/Topography_import_for_Norway#Oppsett) (Norwegian).

## Prerequisites
* Python 2.7 with [NumPy](http://www.numpy.org/)
* [sosi2osm](https://github.com/Gnonthgol/sosi2osm) by [Gnonthgol](https://github.com/Gnonthgol)
* [geographiclib for Python](https://pypi.org/project/geographiclib/)
* [Bidirectional UTM-WGS84 converter for python](https://pypi.org/project/utm/)
* [GDAL - Geospatial Data Abstraction Library](https://www.gdal.org/)

## Usage

### First-time setup (Ubuntu 16.04+)
1. Install `sosi2osm`:
```
sudo apt-get install sosi2osm
```
2. Install the packages `NumPy`, `Geographiclib` and `utm` for Python, e.g. using `pip`:
```
pip install numpy geographiclib utm
```
3. Install GDAL
```
sudo apt install gdal-bin python-gdal
```

### Converting from SOSI to OSM
1. Download the appropriate [N50 SOSI files from Kartverket](https://kartkatalog.geonorge.no/metadata/kartverket/n50-kartdata/ea192681-d039-42ec-b1bc-f3ce04c189ac) and place the zip files in the N50 folder
2. Download the digital elevation models (DEM) files for the same areas as step 1. It's recommended to download the [DTM 10 files from Kartverket](https://kartkatalog.geonorge.no/metadata/kartverket/dtm-10-terrengmodell-utm33/dddbb667-1303-4ac5-8640-7ec04c0e3918). Files for the whole country can be downloaded from [hoydedata.no](https://hoydedata.no/). Extract the DEM files into the DEM folder.
3. Open the kartverket2osm folder in a terminal window, and run parseAll.sh:
```
./parseAll.sh
```

# Components
riverturner.py:
Turns streams and river such that the first node in way is higher than the last point. Requires utm package with small modification (https://github.com/tibnor/utm)

elevation.py:
Finds the elevation of a UTM32 koordinate from statens kartverk DEM files located in child folder DEM.

mergeroad.py:
NOT WORKING. Compares ways in a.osm with b.osm. Outputs ways which are in a.osm and is not close to any similar way in b.osm.
