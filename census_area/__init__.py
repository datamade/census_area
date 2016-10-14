import json
import sys

from census import Census
import esridump
import shapely.geometry

BLOCK_GROUP_URL = 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2014/MapServer/10'

BLOCK_2010_URL = 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Current/MapServer/12'

INCORPORATED_PLACES_TIGER = 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Current/MapServer/28'

TRACT_URL = 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Current/MapServer/8'


class Census(Census):
    def geo_tract(self, fields, geojson_geometry, return_geometry=False):
        filtered_tracts = AreaFilter(geojson_geometry, TRACT_URL)

        features = []
        for tract in filtered_tracts:
            context = {'state' : tract['properties']['STATE'],
                       'county' : tract['properties']['COUNTY']}
            within = 'state:{state} county:{county}'.format(**context)

            tract_id = tract['properties']['TRACT']
            result = self.acs5.get(fields,
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
    
    def geo_blockgroup(self, fields, geojson_geometry):
        filtered_block_groups = AreaFilter(geojson_geometry, BLOCK_GROUP_URL)

        features = []
        for block_group in filtered_block_groups:
            context = {'state' : block_group['properties']['STATE'],
                       'county' : block_group['properties']['COUNTY'],
                       'tract' : block_group['properties']['TRACT']}
            within = 'state:{state} county:{county} tract:{tract}'.format(**context)

            block_group_id = block_group['properties']['BLKGRP']
            result = self.acs5.get(fields,
                                   {'for': 'block group:{}'.format(block_group_id),
                                    'in' :  within})

            if result:
                result, = result
                if return_geometry:
                    block_group['properties'].update(result)
                    features.append(block_group)
                else:
                    features.append(result)

        if return_geometry:
            return {'type': "FeatureCollection", 'features': features}
        else:
            return features

    def geo_block(self, fields, geojson_geometry, return_geometry=False):
        filtered_blocks = AreaFilter(geojson_geometry, BLOCK_2010_URL)

        features = []
        for block in filtered_blocks:
            context = {'state' : block['properties']['STATE'],
                       'county' : block['properties']['COUNTY'],
                       'tract' : block['properties']['TRACT']}
            within = 'state:{state} county:{county} tract:{tract}'.format(**context)

            block_id = '{}{:03d}'.format(block['properties']['BLKGRP'], base_name)
            result = self.sf1.get(fields,
                                  {'for': 'block:{}'.format(block_id),
                                   'in' :  within})

            if result:
                result, = result
                if return_geometry:
                    block['properties'].update(result)
                    features.append(block)
                else:
                    features.append(result)

        if return_geometry:
            return {'type': "FeatureCollection", 'features': features}
        else:
            return features


    def state_place_blockgroup(self, fields, state, place):
        place_dumper = esridump.EsriDumper(INCORPORATED_PLACES_TIGER,
                                           extra_query_args = {'where' : "'{}'".format(place)})
        place = next(iter(place_dumper))
        place_geojson = place['geometry']

        yield from self.geo_blockgroup(self, fields, place_geojson)
        
    def state_place_block(self, fields, state, place, return_geometry=False):
        place_dumper = esridump.EsriDumper(INCORPORATED_PLACES_TIGER,
                                           extra_query_args = {'where' : "NAME='{}'".format(place)})
        place = next(iter(place_dumper))
        place_geojson = place['geometry']

        return self.geo_block(fields, place_geojson, return_geometry)


class AreaFilter(object):
    def __init__(self, geojson_geometry, sub_geography_url):
        self.geo = shapely.geometry.shape(geojson_geometry)

        geo_query_args = {'geometry': ','.join(str(x) for x in self.geo.bounds),
                          'geometryType': 'esriGeometryEnvelope',
                          'spatialRel': 'esriSpatialRelEnvelopeIntersects',
                          'inSR' : '4326',
                          'orderByFields': 'OID'}
        self.area_dumper = esridump.EsriDumper(sub_geography_url,
                                               extra_query_args = geo_query_args)

    def __iter__(self):
        for area in self.area_dumper:
            area_geo = shapely.geometry.shape(area['geometry'])
            if self.geo.intersects(area_geo):
                if self.geo.intersection(area_geo).area/area_geo.area > 0.1:
                    yield area
