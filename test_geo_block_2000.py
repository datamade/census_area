import os
from census_area import SF1Client

API_KEY = os.environ.get('CENSUS_API_KEY')
if not API_KEY:
    raise SystemExit('Set the CENSUS_API_KEY environment variable first.')

# Small polygon covering a few blocks in Chicago's Loop
geometry = {
    'type': 'Polygon',
    'coordinates': [[
        [-87.6320, 41.8827],
        [-87.6290, 41.8827],
        [-87.6290, 41.8850],
        [-87.6320, 41.8850],
        [-87.6320, 41.8827],
    ]]
}

client = SF1Client(API_KEY)

print('Querying geo_block for year 2000...')
results = list(client.geo_block(['P001001'], geometry, year=2000))
print(f'Found {len(results)} blocks\n')

for block, result, proportion in results:
    props = block['properties']
    print(f"Block {props['STATE']}{props['COUNTY']}{props['TRACT']}{props['BLOCK']}"
          f"  population={result.get('P001001', 'N/A')}"
          f"  overlap={proportion:.1%}")
