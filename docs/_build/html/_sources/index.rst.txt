Census Areas Documentation
==========================

This Python library extends the `Census API Wrapper <https://github.com/sunlightlabs/census/>`_
to allow querying Census tracts, block groups, and blocks by Census place, as
well as by arbitrary geographies.

Setup
-----

Get the library and its dependencies using `pip <https://pypi.python.org/pypi/pip>`_:

::

    pip install census_area

Usage
-----

::

   from census_area import Census

   c = Census("MY_API_KEY")
   old_homes = c.acs5.state_place_tract(
      ('NAME', 'B25034_010E'), 17, 14000
   )

The call above will return the name of the census tract and the number of homes
that were built before 1939 for every tract in the City of Chicago. ``17`` is
the FIPS code for Illinois and ``14000`` is the FIPS code for Chicago.

By default, this method will return a list of dictionaries, where each
dictionary represents the data for one tract.

With the ``return_geometry`` argument, you can have the method return a
geojson-like dictionary. Each tract is a feature, and the census variables
about the tract appear in the feature's property attributes.
::

   old_homes_geojson = c.acs5.state_place_tract(
      ('NAME', 'B25034_010E'), 17, 14000,
      return_geometry=True
   )

There are similar methods for block groups –
::

   old_home_block_groups = c.acs5.state_place_blockgroup(
      ('NAME', 'B25034_010E'), 17, 14000
   )

– and blocks.
::

   owner_occupied = c.sf1.state_place_block(
      ('NAME', 'H016F0002'), 17, 14000
   )

Note that block-level geographies are only available for the
short-form data from the Decennial Census and redistricting summary files.

.. list-table:: Summary of Available Geographic Resolutions
   :widths: 25 25 25 25
   :header-rows: 1

   * - Series
     - Tract
     - Block Group
     - Block
   * - ACS 5-Year Estimates
     - ✅
     - ✅
     -
   * - Decennial Census Short Form
     - ✅
     - ✅
     - ✅
   * - Redistricting Summary Files
     - ✅
     - ✅
     - ✅

In addition to these convenient methods, there are lower level methods to
get census tracts, blocks, and groups for arbitrary geometries: ``geo_tract()``,
``geo_blockgroup()``, ``geo_block()``.

Consider this example:

::

   import json

   with open('my_shape.geojson') as infile:
      my_shape_geojson = json.load(infile)

   features = []

   # N.b., your geometry must be in ESPG:4326
   old_homes = c.acs5.geo_tract(
      ('NAME', 'B25034_010E'), my_shape_geojson['geometry']
   )

   for tract_geojson, tract_data, tract_proportion in old_homes:
      tract_geojson['properties'].update(tract_data)
      features.append(tract)

   my_shape_with_new_data_geojson = {
      'type': 'FeatureCollection',
      'features': features
   }


The ``geo_tract()`` method takes in the census variables you want and a
geojson geometry, and returns a **generator** of the tract shapes, as geojson
features, and the variables for that tract. Additionally, the generator returns
a "tract proportion"; this is the proportion of the area of the tract that falls
within your target shape.

``geo_block()`` and ``geo_blockgroup()`` work in the same manner.

API
===

:class:`Census` Object
----------------------

.. automodule:: census_area
   :members:


:class:`ACS5Client` Object
--------------------------

.. autoclass:: census_area.core.ACS5Client

   .. automethod:: state_place_tract

   .. automethod:: state_place_blockgroup

   .. automethod:: geo_tract

   .. automethod:: geo_blockgroup


:class:`SF1Client` Object
-------------------------

.. autoclass:: census_area.core.SF1Client

   .. automethod:: state_place_tract

   .. automethod:: state_place_blockgroup

   .. automethod:: state_place_block

   .. automethod:: geo_tract

   .. automethod:: geo_blockgroup

   .. automethod:: geo_block


:class:`PLClient` Object
------------------------

.. autoclass:: census_area.core.PLClient

   .. automethod:: state_place_tract

   .. automethod:: state_place_blockgroup

   .. automethod:: state_place_block

   .. automethod:: geo_tract

   .. automethod:: geo_blockgroup

   .. automethod:: geo_block


.. toctree::
   :maxdepth: 2

   index
