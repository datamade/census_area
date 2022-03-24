import logging
import collections
from functools import lru_cache

import census
from census.core import supported_years
import esridump

from .lodes import OnTheMap
from .core import AreaFilter, GEO_URLS

from logging import NullHandler

logging.getLogger(__name__).addHandler(NullHandler())

class HashDict(dict):

    def __hash__(self):
        return hash(tuple(self.items()))


class GeoClient(census.core.Client):

    @lru_cache
    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)

    @supported_years(2020, 2019, 2018, 2017, 2016, 2015, 2014, 2013, 2012, 2011, 2010, 2000)
    def geo_tract(self, fields, geojson_geometry, year=None, **kwargs):
        if year is None:
            year = self.default_year

        filtered_tracts = AreaFilter(geojson_geometry,
                                     GEO_URLS['tracts'][year])


        for tract, intersection_proportion in filtered_tracts:
            context = {'state': tract['properties']['STATE'],
                       'county': tract['properties']['COUNTY']}
            within = 'state:{state} county:{county}'.format(**context)

            tract_id = tract['properties']['TRACT']
            result = self.get(fields,
                              HashDict({'for': 'tract:{}'.format(tract_id),
                                        'in': within}),
                              year,
                              **kwargs)

            if result:
                result, = result
            else:
                result = {}

            yield tract, result, intersection_proportion

    @supported_years(2020, 2019, 2018, 2017, 2016, 2015, 2014, 2013, 2012, 2011, 2010)
    def geo_blockgroup(self, fields, geojson_geometry, year=None, **kwargs):
        if year is None:
            year = self.default_year

        filtered_block_groups = AreaFilter(geojson_geometry,
                                           GEO_URLS['block groups'][year])

        for block_group, intersection_proportion in filtered_block_groups:
            context = {'state': block_group['properties']['STATE'],
                       'county': block_group['properties']['COUNTY'],
                       'tract': block_group['properties']['TRACT']}
            within = 'state:{state} county:{county} tract:{tract}'.format(**context)

            tract_blockgroups = self.get(fields,
                                         HashDict({'for': 'block group:*',
                                                   'in':  within}),
                                         year,
                                         **kwargs)

            result = [result for result in tract_blockgroups
                      if result['block group'] == block_group['properties']['BLKGRP']]

            if result:
                result, = result
            else:
                result = {}

            yield block_group, result, intersection_proportion

    def _state_place_area(self, method, fields, state, place, year=None, return_geometry=False, **kwargs):
        if year is None:
            year = self.default_year

        search_query = "PLACE='{}' AND STATE={}".format(place, state)
        place_dumper = esridump.EsriDumper(GEO_URLS['incorporated places'][year],
                                           extra_query_args={'where': search_query,
                                                             'orderByFields': 'OID'})

        try:
            place = next(iter(place_dumper))
        except TypeError as e:
            if "'<' not supported between instances of 'NoneType' and 'NoneType'" in str(e):
                raise ValueError(f'Could not find specified place "{place}" in state "{state}"')

            raise e

        logging.info(place['properties']['NAME'])
        place_geojson = place['geometry']

        areas = method(fields, place_geojson, year, **kwargs)

        features = []
        for i, (feature, result, _) in enumerate(areas):
            if return_geometry:
                feature['properties'].update(result)
                features.append(feature)
            else:
                features.append(result)
            if i % 100 == 0:
                logging.info('{} features'.format(i))

        if return_geometry:
            return {'type': "FeatureCollection", 'features': features}
        else:
            return features

    def geo(self, fields, geojson_geometry, year=None, resolution='tract', ignore_missing = False, **kwargs):
        if year is None:
            year = self.default_year

        fields = census.core.list_or_str(fields)

        as_acs = kwargs.get('as_acs', False)
        if as_acs:
            acs_fields = self._cross(fields)
            for field in acs_fields:
                if self._field_type(field, year) is not int:
                    raise ValueError('{} is not a variable that can be aggregated your geography'.format(field))
        else:
            for field in fields:
                if self._field_type(field, year) is not int:
                    raise ValueError('{} is not a variable that can be aggregated your geography'.format(field))

        resolutions = {'tract': self.geo_tract,
                       'blockgroup': self.geo_blockgroup}

        try:
            geo_units = resolutions[resolution]
        except KeyError:
            raise ValueError('{} is not a valid resolution. Choose one of {}'.format(resolution, resolution.keys()))

        features = geo_units(fields, geojson_geometry, year=year, **kwargs)

        return self._aggregate(fields, features, year, ignore_missing)

    def _aggregate(self, fields, features, year, ignore_missing):
        aggregated_features = collections.defaultdict(list)
        for _, feature in features:
            if ignore_missing and None in feature.values():
                continue
            for field in fields:
                aggregated_features[field].append(feature[field])

        collapsed = {}

        for field in fields:
            if field.endswith('E'):
                agg = sum(aggregated_features[field])
            elif field.endswith('M'):
                e_field = field[:-1] + 'E'
                agg = census.math.moe_of_sum(aggregated_features[e_field],
                                             aggregated_features[field])
            else:
                raise ValueError("Don't know how to aggregate this variable {}".format(feature))

            collapsed[field] = agg

        return collapsed


class ACS5Client(census.core.ACS5Client, GeoClient):

    @supported_years(2019, 2018, 2017, 2016, 2015, 2014, 2013, 2012, 2011, 2010)
    def state_place_tract(self, *args, **kwargs):
        return self._state_place_area(self.geo_tract, *args, **kwargs)

    @supported_years(2019, 2018, 2017, 2016, 2015, 2014, 2013, 2012, 2011, 2010)
    def state_place_blockgroup(self, *args, **kwargs):
        return self._state_place_area(self.geo_blockgroup, *args, **kwargs)


class GeoBlockClient(GeoClient):

    @supported_years(2020, 2010)
    def geo_block(self, fields, geojson_geometry, year):
        if year is None:
            year = self.default_year

        filtered_blocks = AreaFilter(geojson_geometry,
                                     GEO_URLS['blocks'][year])

        for block, intersection_proportion in filtered_blocks:
            context = {'state': block['properties']['STATE'],
                       'county': block['properties']['COUNTY'],
                       'tract': block['properties']['TRACT']}
            within = 'state:{state} county:{county} tract:{tract}'.format(**context)

            tract_blocks = self.get(fields,
                                    HashDict({'for': 'block:*',
                                              'in':  within}),
                                    year)
            
            result = [result for result in tract_blocks
                      if result['block'] == block['properties']['BLOCK']]

            if result:
                result, = result
            else:
                breakpoint()
                result = {}

            yield block, result, intersection_proportion
    

class SF1Client(census.core.SF1Client, GeoBlockClient):
    @supported_years(2010)
    def state_place_tract(self, *args, **kwargs):
        return self._state_place_area(self.geo_tract, *args, **kwargs)

    @supported_years(2010)
    def state_place_blockgroup(self, *args, **kwargs):
        return self._state_place_area(self.geo_blockgroup, *args, **kwargs)

    @supported_years(2010)
    def state_place_block(self, *args, **kwargs):
        return self._state_place_area(self.geo_block, *args, **kwargs)

            
class PLClient(census.core.PLClient, GeoBlockClient):
    @supported_years(2020, 2010)
    def state_place_tract(self, *args, **kwargs):
        return self._state_place_area(self.geo_tract, *args, **kwargs)

    @supported_years(2020, 2010)
    def state_place_blockgroup(self, *args, **kwargs):
        return self._state_place_area(self.geo_blockgroup, *args, **kwargs)

    @supported_years(2020, 2010)
    def state_place_block(self, *args, **kwargs):
        return self._state_place_area(self.geo_block, *args, **kwargs)


class Census(census.Census):
    def __init__(self, key, year=None, session=None):
        super(Census, self).__init__(key, year, session)
        self.acs5 = ACS5Client(key, year, session)
        self.sf1 = SF1Client(key, year, session)
        self.pl = PLClient(key, year, session)
