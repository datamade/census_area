import shapely.geometry
import shapely.geos
import esridump

GEO_URLS = {
    'tracts': {
        1990: 'https://gis.uspatial.umn.edu/arcgis/rest/services/nhgis/Census_Tracts_1910_2014/MapServer/8',
        2000: 'https://tigerweb.geo.census.gov/arcgis/rest/services/Census2010/tigerWMS_Census2000/MapServer/6',
        2010: 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census2010/MapServer/14',
        2011: 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census2010/MapServer/14',
        2012: 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census2010/MapServer/14',
        2013: 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2013/MapServer/8',
        2014: 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2014/MapServer/8',
        2015: 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2015/MapServer/8',
        2016: 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2016/MapServer/8',
        2017: 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2017/MapServer/8',
        2018: 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2018/MapServer/8',
        2019: 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2019/MapServer/8',
        },
    'block groups': {
        2000: 'https://tigerweb.geo.census.gov/arcgis/rest/services/Census2010/tigerWMS_Census2000/MapServer/8',
        2010: 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census2010/MapServer/16',
        2011: 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census2010/MapServer/16',
        2012: 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census2010/MapServer/16',
        2013: 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2013/MapServer/10',
        2014: 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2014/MapServer/10',
        2015: 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2015/MapServer/10',
        2016: 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2016/MapServer/10',
        2017: 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2017/MapServer/10',
        2018: 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2017/MapServer/10',
        2019: 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2018/MapServer/10',
        },
    'blocks': {
        2000: 'https://tigerweb.geo.census.gov/arcgis/rest/services/Census2010/tigerWMS_Census2000/MapServer/10',
        2010: 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Current/MapServer/12'},
    'incorporated places': {
        1990: 'https://gis.uspatial.umn.edu/arcgis/rest/services/nhgis/Places_1980_2014/MapServer/1',
        2000: 'https://tigerweb.geo.census.gov/arcgis/rest/services/Census2010/tigerWMS_Census2000/MapServer/24',
        2010: 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census2010/MapServer/34',
        2011: 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census2010/MapServer/34',
        2012: 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_Census2010/MapServer/34',
        2013: 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2013/MapServer/26',
        2014: 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2014/MapServer/26',
        2015: 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2015/MapServer/26',
        2016: 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2016/MapServer/26',
        2017: 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2017/MapServer/26',
        2018: 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2017/MapServer/28',
        2019: 'https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/tigerWMS_ACS2017/MapServer/28',
    }
}


class AreaFilter(object):
    def __init__(self, geojson_geometry, sub_geography_url):
        self.geo = shapely.geometry.shape(geojson_geometry)

        geo_query_args = {'geometry': ','.join(str(x) for x in self.geo.bounds),
                          'geometryType': 'esriGeometryEnvelope',
                          'spatialRel': 'esriSpatialRelEnvelopeIntersects',
                          'inSR': '4326',
                          'geometryPrecision': 9,
                          'orderByFields': 'OID'}
        self.area_dumper = esridump.EsriDumper(sub_geography_url,
                                               extra_query_args=geo_query_args)

    def __iter__(self):
        for area in self.area_dumper:
            area_geo = shapely.geometry.shape(area['geometry'])
            if self.geo.intersects(area_geo):
                try:
                    intersection = self.geo.intersection(area_geo)
                except shapely.geos.TopologicalError:
                    intersection = self.geo.buffer(0).intersection(area_geo.buffer(0))
                intersection_proportion = intersection.area / area_geo.area
                if intersection_proportion > 0.01:
                    yield area, intersection_proportion
