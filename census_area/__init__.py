from census import Census
from .geojson2esri import geojson2esri
import esridump
import json
import sys
import shapely.geometry

BLOCK_GROUP_URL = 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2014/MapServer/10'

BLOCK_2010_URL = 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Current/MapServer/12'

INCORPORATED_PLACES_TIGER = 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Current/MapServer/28'


class Census(Census):
    def geo_blockgroup(self, fields, geojson_geometry):
        geo = shapely.geometry.shape(geojson_geometry)
        geo_query_args = {'geometry': ',|'.join(str(x) for x in geo.bounds),
                          'geometryType': 'esriGeometryEnvelope',
                          'spatialRel': 'esriSpatialRelEnvelopeIntersects',
                          'inSR' : '4326',
                          'orderByFields': 'OID'}
        bg_dumper = esridump.EsriDumper(BLOCK_GROUP_URL,
                                        extra_query_args = geo_query_args)

        for block_group in bg_dumper:
            block_group_geojson = block_group['geometry']
            block_group_geo = shapely.geometry.shape(block_group_geojson)
            if geo.intersects(block_group_geo):
                context = {'state' : row['properties']['STATE'],
                           'county' : row['properties']['COUNTY'],
                           'tract' : row['properties']['TRACT']}
                within = 'state:{state} county:{county} tract:{tract}'.format(**context)

                block_group = row['properties']['BLKGRP']
                (result,) = self.acs5.get(fields,
                                          {'for': 'block group:{}'.format(block_group),
                                           'in' :  within})

                yield result

    def geo_block(self, fields, geojson_geometry, return_geometry=False):
        geo = shapely.geometry.shape(geojson_geometry)
        geo_query_args = {'geometry': ',|'.join(str(x) for x in geo.bounds),
                          'geometryType': 'esriGeometryEnvelope',
                          'spatialRel': 'esriSpatialRelEnvelopeIntersects',
                          'inSR' : '4326',
                          'orderByFields': 'OID'}
        block_dumper = esridump.EsriDumper(BLOCK_GROUP_URL,
                                           extra_query_args = geo_query_args)
        features = []
        num_blocks = 0
        for block in block_dumper:
            block_geojson = block['geometry']
            block_geo = shapely.geometry.shape(block_geojson)
            base_name = int(block['properties']['BASENAME'])
            if base_name and geo.intersects(block_geo):
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
                    num_blocks += 1
                    if num_blocks % 100 == 0:
                        print('{} Blocks'.format(num_blocks), file=sys.stderr)
                    if return_geometry:
                        block['properties'].update(result)
                        features.append(block)
                    else:
                        features.append(block)

        if return_geometry:
            return {'type': "FeatureCollection", 'features': features}
        else:
            return features
                

    def state_place_blockgroup(self, fields, state, place):
        place_dumper = esridump.EsriDumper(INCORPORATED_PLACES_TIGER,
                                           extra_query_args = {'where' : "'{}'".format(place)})
        place = next(place_dumper)
        place_geojson = esridump.esri2geojson(place['geometry']['coordinates'])

        yield from self.geo_blockgroup(self, fields, place_geojson)
        
    def state_place_block(self, fields, state, place, return_geometry=False):
        place_dumper = esridump.EsriDumper(INCORPORATED_PLACES_TIGER,
                                           extra_query_args = {'where' : "NAME='{}'".format(place)})
        place = next(iter(place_dumper))
        place_geojson = place['geometry']

        return self.geo_block(fields, place_geojson, return_geometry)
