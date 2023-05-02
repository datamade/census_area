import json
import logging
import os

import click

from census_area import Census

CENSUS_API_KEY = os.getenv("CENSUS_API_KEY")

def set_logging_level(verbose, quiet):

    root_logger = logging.getLogger()
    handler = logging.StreamHandler()
    root_logger.addHandler(handler)

    if verbose >= 2:
        handler.setLevel(logging.DEBUG)
    elif verbose == 1:
        handler.setLevel(logging.INFO)
    elif quiet >= 1:
        handler.setLevel(logging.ERROR)
    else:
        handler.setLevel(logging.WARNING)


@click.command()
@click.option("-f", "--field", multiple=True, type=str)
@click.option("-s", "--state", type=str, required=True)
@click.option("-p", "--place", type=str, required=True)
@click.option("-v", "--verbose", count=True, help="verbosity level")
@click.option("-q", "--quiet", count=True, help="quiet level")
def main(field, state, place, verbose, quiet):
    if verbose and quiet:
        raise click.UsageError("can't set both -v and -q flags")

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    set_logging_level(verbose, quiet)
    
    variables = ("NAME",) + tuple(field)
    census = Census(CENSUS_API_KEY)
    data = census.acs5.state_place_tract(variables, state, place, return_geometry=True)
    click.echo(json.dumps(data))
