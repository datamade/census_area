import pytest
from unittest.mock import patch, MagicMock

from census_area import PLClient
from census_area.variables import GEO_URLS


TEST_GEOMETRY = {
    'type': 'Polygon',
    'coordinates': [[
        [-87.65, 41.85],
        [-87.64, 41.85],
        [-87.64, 41.86],
        [-87.65, 41.86],
        [-87.65, 41.85],
    ]]
}


def make_block_feature(state='17', county='031', tract='839100', block='1001'):
    return {
        'type': 'Feature',
        'geometry': {
            'type': 'Polygon',
            'coordinates': [[
                [-87.649, 41.850],
                [-87.641, 41.850],
                [-87.641, 41.859],
                [-87.649, 41.859],
                [-87.649, 41.850],
            ]]
        },
        'properties': {
            'STATE': state,
            'COUNTY': county,
            'TRACT': tract,
            'BLOCK': block,
        }
    }


@pytest.fixture
def client():
    return PLClient('fake_api_key')


@pytest.mark.parametrize('year', [2000, 2010, 2020])
def test_geo_block_uses_correct_url_for_year(client, year):
    with patch('census_area.core.AreaFilter') as MockAreaFilter, \
         patch.object(client, 'get', return_value=[]):
        MockAreaFilter.return_value = []
        list(client.geo_block(['P001001'], TEST_GEOMETRY, year=year))
        MockAreaFilter.assert_called_once_with(TEST_GEOMETRY, GEO_URLS['blocks'][year])


def test_geo_block_yields_block_result_and_proportion(client):
    block_feature = make_block_feature()
    census_data = [{'state': '17', 'county': '031', 'tract': '839100',
                    'block': '1001', 'P001001': '42'}]

    with patch('census_area.core.AreaFilter') as MockAreaFilter, \
         patch.object(client, 'get', return_value=census_data):
        MockAreaFilter.return_value = [(block_feature, 0.75)]
        results = list(client.geo_block(['P001001'], TEST_GEOMETRY, year=2020))

    assert len(results) == 1
    block, result, proportion = results[0]
    assert block == block_feature
    assert result['P001001'] == '42'
    assert proportion == 0.75


def test_geo_block_2000(client):
    block_feature = make_block_feature()
    census_data = [{'state': '17', 'county': '031', 'tract': '839100',
                    'block': '1001', 'P001001': '42'}]

    with patch('census_area.core.AreaFilter') as MockAreaFilter, \
         patch.object(client, 'get', return_value=census_data):
        MockAreaFilter.return_value = [(block_feature, 1.0)]
        results = list(client.geo_block(['P001001'], TEST_GEOMETRY, year=2000))

    assert len(results) == 1
    _, result, proportion = results[0]
    assert result['P001001'] == '42'
    assert proportion == 1.0


def test_geo_block_empty_result_when_block_not_in_census_response(client):
    block_feature = make_block_feature(block='1001')
    census_data = [{'state': '17', 'county': '031', 'tract': '839100',
                    'block': '9999', 'P001001': '10'}]

    with patch('census_area.core.AreaFilter') as MockAreaFilter, \
         patch.object(client, 'get', return_value=census_data):
        MockAreaFilter.return_value = [(block_feature, 1.0)]
        results = list(client.geo_block(['P001001'], TEST_GEOMETRY, year=2020))

    assert len(results) == 1
    _, result, _ = results[0]
    assert result == {}


def test_geo_block_unsupported_year_raises(client):
    with pytest.raises(Exception):
        list(client.geo_block(['P001001'], TEST_GEOMETRY, year=1990))
