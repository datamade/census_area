import json
import sys
import logging

import census
from census.core import supported_years

import esridump
import shapely.geometry
import shapely.geos

try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())

TRACT_URLS = {2010 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census2010/MapServer/14',
              2013 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2013/MapServer/8',
              2014 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2014/MapServer/8',
              2015 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2015/MapServer/8',
              2016 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2015/MapServer/8'}

BLOCK_GROUP_URLS = {2010 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census2010/MapServer/16',
                    2013 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2013/MapServer/10',
                    2014 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2014/MapServer/10',
                    2015 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2015/MapServer/10',
                    2016 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2015/MapServer/10'}

BLOCK_URLS = {2010 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Current/MapServer/12'}

              
INCORPORATED_PLACES_URLS = {2010 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census2010/MapServer/34',
                            2013 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2013/MapServer/26',
                            2014 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2014/MapServer/26',
                            2015 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2015/MapServer/26',
                            2016 : 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2016/MapServer/26'}



class AreaFilter(object):
    def __init__(self, geojson_geometry, sub_geography_url):
        self.geo = shapely.geometry.shape(geojson_geometry)

        geo_query_args = {'geometry': ','.join(str(x) for x in self.geo.bounds),
                          'geometryType': 'esriGeometryEnvelope',
                          'spatialRel': 'esriSpatialRelEnvelopeIntersects',
                          'inSR' : '4326',
                          'geometryPrecision' : 9,
                          'orderByFields': 'OID'}
        self.area_dumper = esridump.EsriDumper(sub_geography_url,
                                               extra_query_args = geo_query_args)

    def __iter__(self):
        for area in self.area_dumper:
            area_geo = shapely.geometry.shape(area['geometry'])
            if self.geo.intersects(area_geo):
                try:
                    intersection = self.geo.intersection(area_geo)
                except shapely.geos.TopologicalError:
                    intersection = self.geo.buffer(0).intersection(area_geo.buffer(0))
                if intersection.area/area_geo.area > 0.1:
                    yield area

class GeoClient(census.core.Client):
    def geo_tract(self, fields, geojson_geometry, return_geometry=False):
        filtered_tracts = AreaFilter(geojson_geometry,
                                     TRACT_URLS[self.default_year])

        features = []
        for tract in filtered_tracts:
            context = {'state' : tract['properties']['STATE'],
                       'county' : tract['properties']['COUNTY']}
            within = 'state:{state} county:{county}'.format(**context)

            tract_id = tract['properties']['TRACT']
            result = self.get(fields,
                              {'for': 'tract:{}'.format(tract_id),
                               'in' :  within})

            if result:
                result, = result
                if return_geometry:
                    tract['properties'].update(result)
                    features.append(tract)
                else:
                    features.append(result)

        if return_geometry:
            return {'type': "FeatureCollection", 'features': features}
        else:
            return features


    def geo_blockgroup(self, fields, geojson_geometry, return_geometry=False):
        filtered_block_groups = AreaFilter(geojson_geometry,
                                           BLOCK_GROUP_URLS[self.default_year])

        features = []
        for i, block_group in enumerate(filtered_block_groups):
            context = {'state' : block_group['properties']['STATE'],
                       'county' : block_group['properties']['COUNTY'],
                       'tract' : block_group['properties']['TRACT']}
            within = 'state:{state} county:{county} tract:{tract}'.format(**context)

            block_group_id = block_group['properties']['BLKGRP']
            
            result = self.get(fields,
                              {'for': 'block group:{}'.format(block_group_id),
                               'in' :  within})

            if result:
                result, = result
                if return_geometry:
                    block_group['properties'].update(result)
                    features.append(block_group)
                else:
                    features.append(result)

            if i % 100 == 0:
                logging.info('{} block groups'.format(i))
                    

        if return_geometry:
            return {'type': "FeatureCollection", 'features': features}
        else:
            return features

    def geo_block(self, fields, geojson_geometry, return_geometry=False):
        filtered_blocks = AreaFilter(geojson_geometry,
                                     BLOCK_URLS[self.default_year])

        features = []
        for i, block in enumerate(filtered_blocks):
            context = {'state' : block['properties']['STATE'],
                       'county' : block['properties']['COUNTY'],
                       'tract' : block['properties']['TRACT']}
            within = 'state:{state} county:{county} tract:{tract}'.format(**context)

            block_id = block['properties']['BLOCK']
            result = self.get(fields,
                              {'for': 'block:{}'.format(block_id),
                               'in' :  within})

            if result:
                result, = result
                if return_geometry:
                    block['properties'].update(result)
                    features.append(block)
                else:
                    features.append(result)

            if i % 100 == 0:
                logging.info('{} blocks'.format(i))

        if return_geometry:
            return {'type': "FeatureCollection", 'features': features}
        else:
            return features

    def _state_place_area(self, method, fields, state, place, return_geometry=False):
        search_query = "NAME='{}' AND STATE={}".format(place, state)
        place_dumper = esridump.EsriDumper(INCORPORATED_PLACES_URLS[self.default_year],
                                           extra_query_args = {'where' : search_query,
                                                               'orderByFields': 'OID'})

        place = next(iter(place_dumper))
        logging.info(place['properties']['NAME'])
        place_geojson = place['geometry']

        return method(fields, place_geojson, return_geometry)
        
class ACS5Client(census.core.ACS5Client, GeoClient):

    @supported_years(2014, 2013, 2010)
    def state_place_tract(self, *args, **kwargs):
        return self._state_place_area(self,geo_tract, *args, **kwargs)

    @supported_years(2014, 2013, 2010)
    def state_place_blockgroup(self, *args, **kwargs):
        return self._state_place_area(self.geo_blockgroup, *args, **kwargs)

class SF1Client(census.core.SF1Client, GeoClient):
    @supported_years(2010)
    def state_place_tract(self, *args, **kwargs):
        return self._state_place_area(self,geo_tract, *args, **kwargs)

    @supported_years(2010)
    def state_place_blockgroup(self, *args, **kwargs):
        return self._state_place_area(self.geo_blockgroup, *args, **kwargs)

    @supported_years(2010)
    def state_place_block(self, *args, **kwargs):
        return self._state_place_area(self.geo_block, *args, **kwargs)

class Census(census.Census):
    def __init__(self, key, year=None, session=None):
        super(Census, self).__init__(key, year, session)
        self.acs5 = ACS5Client(key, year, session)
        self.sf1 = SF1Client(key, year, session)
