import copy
from esridump.esri2geojson import ring_is_clockwise

geojson_types = {'Point': 'esriGeometryPoint',
                 'MultiPoint': 'esriGeometryMultiPoint',
                 'LineString': 'esriGeometryPolyLine',
                 'MultiLineString': 'esriGeometryPolyLine',
                 'Polygon': 'esriGeometryPolygon',
                 'MultiPolygon': 'esriGeometryPolygon'}


def geojson2esri(geojson_geometry):
    geojson_geometry = copy.deepcopy(geojson_geometry)
    if geojson_geometry['type'] in geojson_types:
        response = convert_geojson_geometry(geojson_geometry)
        response['spatialReference'] = {'wkid' : 4326}
        return response, geojson_types[geojson_geometry['type']]

def convert_geojson_geometry(geojson_geometry):
    if geojson_geometry is None:
        return geojson_geometry
    elif geojson_geometry['type'] == 'Point':
        return convert_geojson_point(geojson_geometry)
    elif geojson_geometry['type'] == 'MultiPoint':
        return convert_geojson_multipoint(geojson_geometry)
    elif geojson_geometry['type'] in {'LineString', 'MultiLineString'}:
        return convert_geojson_lines(geojson_geometry)
    elif geojson_geometry['type'] == 'Polygon':
        return convert_geojson_polygon(geojson_geometry)
    elif geojson_geometry['type'] == 'MultiPolygon':
        return convert_geojson_multipolygon(geojson_geometry)


def convert_geojson_point(geojson_geometry):
    x_coord, y_coord = geojson_geometry.get('coordinates')

    if x_coord and y_coord:
        return {
            "x": x_coord,
            "y": y_coord
        }
    else:
        return None

def convert_geojson_multipoint(geojson_geometry):
    coordinates = geojson_geometry.get('coordinates')

    return {
        "points": coordinates
        }

def convert_geojson_lines(geojson_geometry):
    coordinates = geojson_geometry.get('coordinates')

    return {
        "paths": coordinates
    }

def convert_geojson_polygon(geojson_geometry):
    coordinates = geojson_geometry.get('coordinates')

    if not ring_is_clockwise(coordinates):
        coordinates.reverse()

    return {
        "rings": [coordinates]
    }


def convert_geojson_multipolygon(geojson_geometry):
    coordinates = geojson_geometry.get('coordinates')

    # Esri doesn't support distinct islands
    coordinates = coordinates[0] 

    first_ring = coordinates.pop(0)
    if not ring_is_clockwise(first_ring):
        first_ring.reverse()

    rings = [first_ring]

    for ring in coordinates:
        if ring_is_clockwise(ring):
            ring.reverse()
        rings.append(ring)
        

    return {
        "rings": rings
    }
