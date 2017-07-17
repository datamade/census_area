import json
import io
import csv
import functools

import requests
import zipfile
import shapefile
import shapely.geometry
import shapely.ops
import pyproj

from .core import AreaFilter, GEO_URLS
from .variables import LODES_VARIABLES

class OnTheMap(requests.Session):
    BASE = 'https://onthemap.ces.census.gov'

    JOB_TYPES = {'all': 'jt00',
                 'primary': 'jt01',
                 'private': 'jt02',
                 'private primary': 'jt03'}

    def _select_area(self, geojson_geometry):
        url = self.BASE + '/cgi-bin/select.py'

        geom = shapely.geometry.shape(geojson_geometry)
        geom = project(geom)

        data = {"wkt": geom.wkt}

        response = self.post(url, json=data)

        selection_id = response.json()[0]['selection_id']

        return selection_id

    def _report(self, selection_id, area, origin, job_type, year):
        url = self.BASE + '/cgi-bin/report.py'

        if area:
            analysis_type = 'area_profile_report'
        else:
            analysis_type = 'distance_direction_report'

        report_settings = {"origin_type": origin,
                           "origin_dir": "home",
                           "analysis_type": analysis_type,
                           "ap_segment": "s000",
                           "comparison_geom": "us_plc",
                           "ac_segment": "s000",
                           "destination_rollup": "us_plc",
                           "year": [year],
                           "job_type": self.JOB_TYPES[job_type],
                           "geom_operation": "ignore",
                           "selection": [selection_id],
                           "color":["#0000AA"]}

        data = {'mode': 'generate',
                'settings': json.dumps(report_settings)}

        response = self.post(url, data=data)

        report_id = response.json()['report_id']

        return report_id

    def _area(self, report_id, year):

        url = self.BASE + '/cgi-bin/report.py'

        analysis = {"analysis_type": "area_profile_report",
                    "job_type": 'jt00',
                    "ap_segment": "s000",
                    "origin": 'home',
                    "color": ["#0000AA"]}

        params = {'report_id': report_id,
                  'settings': json.dumps(analysis),
                  'mode': 'export_geography',
                  'format': 'shp'}

        response = self.get(url, params=params)

        z = zipfile.ZipFile(io.BytesIO(response.content))

        with z.open('points_{year}.dbf'.format(year=year)) as dbf:
            reader = shapefile.Reader(dbf=io.BytesIO(dbf.read()))
            fields = [field[0] for field in reader.fields[1:]]
            for row in reader.records():
                yield dict(zip(fields, row))

    def _od(self, report_id, year):

        url = self.BASE + '/cgi-bin/report.py'

        analysis = {"labor": "s000",
                    "year": 2014,
                    "analysis_type": "distance_direction_report",
                    "job_type": 'jt01',
                    "origin_type": 'work',
                    "distance":"all",
                    "color":["#0000AA"]}

        params = {'report_id': report_id,
                  'settings': json.dumps(analysis),
                  'mode': 'export_geography',
                  'format': 'shp'}

        response = self.get(url, params=params)

        z = zipfile.ZipFile(io.BytesIO(response.content))

        with z.open('points_{year}.dbf'.format(year=year)) as dbf:
            reader = shapefile.Reader(dbf=io.BytesIO(dbf.read()))
            fields = [field[0] for field in reader.fields[1:]]
            for row in reader.records():
                yield dict(zip(fields, row))

    def _geojson(self, geojson_geometry, reader):
        blocks = AreaFilter(geojson_geometry,
                            GEO_URLS['blocks'][2010])

        data = {}
        for block in reader:
            block_id = block.pop('id')
            data[block_id] = block

        features = []
        for feature in blocks:
            block_id = feature['properties']['GEOID']
            if block_id in data:
                legible = {LODES_VARIABLES[k]: v
                           for k, v
                           in data[block_id].items()}
                feature['properties'].update(legible)
                features.append(feature)


        return {'type': "FeatureCollection", 'features': features}

        

    def area_query(self, geojson, area='work', job_type='all', year=2014):
        selection_id = self._select_area(geojson)
        report_id = self._report(selection_id, True, area, job_type, year)
        reader = self._area(report_id, year)

        for row in reader:
            yield row

    def od_query(self, geojson, origin='work', job_type='all', year=2014):
        selection_id = self._select_area(geojson)
        report_id = self._report(selection_id, False, origin, job_type, year)
        reader = self._od(report_id, year)

        for row in reader:
            yield row
            
    def residents(self, geojson, job_type='all', year=2014, return_geometry=True):
        reader = self.area_query(geojson, 'home', job_type, year)
        if return_geometry:
            return self._geojson(geojson, reader)
        else:
            return list(reader)

    def workforce(self, geojson, job_type='all', year=2014, return_geometry=True):
        reader = self.area_query(geojson, 'work', job_type, year)
        if return_geometry:
            return self._geojson(geojson, reader)
        else:
            return list(reader)

    def commutes_to(self, geojson, job_type='all', year=2014, return_geometry=True):
        reader = self.od_query(geojson, 'work', job_type, year)
        return list(reader)

    def commutes_from(self, geojson, job_type='all', year=2014, return_geometry=True):
        reader = yield from self.od_query(geojson, 'home', job_type, year)
        return list(reader)

        
def project(geom):
    return shapely.ops.transform(functools.partial(pyproj.transform,
                                                   pyproj.Proj("+init=EPSG:4326"),
                                                   pyproj.Proj("+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=37.5 +lon_0=-96 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs")),
                                 geom)


