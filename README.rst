============
Census Areas
============

This Python library extends the Sunlight Foundation's `Census API Wrapper <https://github.com/sunlightlabs/census/>`_ to allow querying Census tracts, block groups, and blocks by Census place, as well as by  arbitrary geographies.

Setup
======

Get the library and its dependencies using `pip <https://pypi.python.org/pypi/pip>`_:

::

    pip install census_area

Usage
======

::

    from census_area import Census

    c = Census("MY_API_KEY")
    old_homes = c.acs5.state_place_tract(('NAME', 'B25034_010E'), 17, 14000)
    
The call above will return the name of the census tract and the number of homes that were built before 1939 for every tract in the City of Chicago. ``17`` is the FIPS code for Illinois and ``14000`` is the FIPS code for Chicago.

By default, this method will return a list of dictionaries, where each dictionary represents the data for one tract. 

With the ``return_geometry`` argument, you can have the method return a geojson-like dictionary. Each tract is a feature, and the census variables about the tract appear in the feature's property attributes.
::

    old_homes_geojson = c.acs5.state_place_tract(('NAME', 'B25034_010E'), 17, 14000), return_geometry=True)

There are similar methods for block groups
::

    old_home_block_groups = c.acs5.state_place_blockgroup(('NAME', 'B25034_010E'), 17, 14000))

And blocks. Note that block level geographies are only available for the short-form data from the Decennial Census
::
  
    owner_occupied = c.sf1.state_place_block(('NAME', 'H016F0002'), 17, 14000)

The tract and blockgroup methods are also available for the Decennial Census.
::

    owner_occupied_blockgroup = c.sf1.state_place_tract(('NAME', 'H016F0002'), 17, 14000)
    owner_occupied_tract = c.sf1.state_place_blockgroup(('NAME', 'H016F0002'), 17, 14000)
    
    old_homes = c.sf1.state_place_tract('NAME', 'H034010'), 17, 14000)
    old_homes = c.sf1.state_place_blockgroup('NAME', 'H034010'), 17, 14000)

In addition to these convenient methods, there are three lower level ways to get census tracts, blocks, and groups for arbitrary geometries.

::
    
    import json
    
    with open('my_shape.geojson') as infile:
        my_shape_geojson = json.load(infile)
    features = []
    old_homes = c.acs5.geo_tract(('NAME', 'B25034_010E'), my_shape_geojson['geometry'])
    for tract_geojson, tract_data, tract_proportion in old_homes:
         tract_geojson['properties'].update(tract_data)
         features.append(tract)
         
    my_shape_with_new_data_geojson = {'type': "FeatureCollection", 'features': features}
    

The method takes in the census variables you want and a geojson geometry, and returns a **generator** of the tract shapes, as geojson features, and the variables for that tract. Additionally, the generator returns a "tract proportion"; this is the proportion of the area of the tract that falls within your target shape.

Similar methods are provided for block groups and blocks, for the ACS 5-year and Decennial Census.
::

    c.acs5.geo_blockgroup(('NAME', 'B25034_010E'), my_shape_geojson['geometry'])
    
    c.sf1.geo_block(('NAME', 'H016F0002'), my_shape_geojson['geometry'])
    c.sf1.geo_blockgroup(('NAME', 'H016F0002'), my_shape_geojson['geometry'])
    c.sf1.geo_tract(('NAME', 'H016F0002'), my_shape_geojson['geometry'])
    
    c.sf1.state_place_tract('NAME', 'H034010'), my_shape_geojson['geometry'])
    c.sf1.state_place_blockgroup('NAME', 'H034010'), my_shape_geojson['geometry'])

Team
====

* Jean Cochrane, DataMade
* Forest Gregg, DataMade

Errors and bugs
===============

If something is not behaving intuitively, it is a bug and should be reported.
Report it here by creating an issue: https://github.com/datamade/census_area/issues

Help us fix the problem as quickly as possible by following `Mozilla's guidelines for reporting bugs. <https://developer.mozilla.org/en-US/docs/Mozilla/QA/Bug_writing_guidelines#General_Outline_of_a_Bug_Report>`_

Patches and pull requests
=========================

Your patches are welcome. Here's our suggested workflow:

* Fork the project.
* Make your feature addition or bug fix.
* Send us a pull request with a description of your work. Bonus points for topic branches!

Copyright and attribution
=========================

Copyright (c) 2016 DataMade. Released under the `MIT License <https://github.com/datamade/your-repo-here/blob/master/LICENSE>`_.

