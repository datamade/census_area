import logging
import census

from .core import ACS5Client, SF1Client, PLClient


class Census(census.Census):
    '''
    Unified API for accessing Census data

    Attributes:

    * acs5: instance of ACS5Client
    * sf1: instance of SF1Client
    * pl: instance of PLClient
    '''
    def __init__(self, key, year=None, session=None):
        super(Census, self).__init__(key, year, session)
        self.acs5 = ACS5Client(key, year, session)
        self.sf1 = SF1Client(key, year, session)
        self.pl = PLClient(key, year, session)
