from kartograph import Kartograph
from collections import OrderedDict
import subprocess
import csv
import urllib2
import urllib
import fiona
from shapely import geometry
from threading import Timer

'''
1. Open CSV of airport locations
2. For each...
   - get_buffered_bbox of location
   -- get_osm_data
   - osm2shp
   - clean_up
   - create map with kartograph

'''
def get_buffered_bbox(loc):
    bbox = ','.join(str(coord) for coord in geometry.Point(float(loc[2]), float(loc[1])).buffer(0.036207221).envelope.exterior.bounds)
    get_osm_data(loc[0], bbox)

def get_osm_data(place, bbox):
    print place
    url = 'http://overpass-api.de/api/interpreter'
    values = { 'data': 'way[aeroway~"runway|taxiway"](' + bbox + ');(._;>;);out;' }
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    result = response.read()
    with open('osm/' + place + '.osm', 'w') as output:
        output.write(result)
        osm2shp(place)

def osm2shp(place):
    convert = subprocess.Popen(['ogr2ogr -nlt LINESTRING -skipfailures -f "ESRI Shapefile" shapefiles/' + place + ' osm/' + place + '.osm'], shell=True)
    timer = Timer(5.0, clean_up, [place])
    timer.start()

def clean_up(place):
    with fiona.open('shapefiles/' + place + '/lines.shp', 'r') as source:
        source_driver = source.driver
        source_crs = source.crs

        output_schema = {'geometry': 'LineString', 'properties': OrderedDict([(u'osm_id', 'str:80'), (u'p_type', 'str:80'), (u'airport', 'str:80')])}

        with fiona.open('shapefiles/' + place + '/' + place + '_out.shp', 'w', driver=source_driver, crs=source_crs, schema=output_schema) as output:
            for feature in source:
                del feature['properties']['name']
                del feature['properties']['man_made']
                del feature['properties']['highway']
                del feature['properties']['waterway']
                del feature['properties']['aerialway']
                del feature['properties']['barrier']
                tags = feature['properties']['other_tags'].split(",")
                for tag in tags:
                  kv = tag.split("=>")
                  if kv[0].replace('"', '') == "aeroway":
                      feature['properties']['p_type'] = kv[1].replace('"', '')
                del feature['properties']['other_tags']
                feature['properties']['airport'] = 'MSN'
                output.write(feature)
    merp(place)

def merp(place):
    K = Kartograph()
    css = open('styles.css').read()

    config = {
    	'layers': [{
    		'src': 'shapefiles/' + place + '/' + place + '_out.shp',
    		'class': 'runways'
    	}]
    }

    K.generate(config, outfile='svg/' + place + '.svg', stylesheet=css)

with open('airports.csv', 'rb') as input:
    reader = csv.reader(input)
    # name, lon, lat
    for i, airport in enumerate(reader):
        # Skip header row
        if i != 0:
            get_buffered_bbox(airport)
