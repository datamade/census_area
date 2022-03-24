#!/usr/bin/python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError :
    raise ImportError("setuptools module required, please go to https://pypi.python.org/pypi/setuptools and follow the instructions for installing setuptools")

long_description = open('README.rst').read()

setup(
    name='census_area',
    url='https://github.com/datamade/census_area',
    long_description=long_description,
    version='0.4.3',
    author='Forest Gregg',
    author_email='fgregg@datamade.us',
    description='Census data for arbitrary geographies',
    packages=['census_area'],
    install_requires=['esridump',
                      'census',
                      'shapely',
                      'pyshp',
                      'pyproj'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Information Analysis'],
)
