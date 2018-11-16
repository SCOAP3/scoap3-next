from __future__ import absolute_import, print_function

import click
import json
import sys

from flask.cli import with_appcontext
from scoap3.modules.records.util import create_from_json


@click.group()
def loadrecords():
    """Migration commands."""


@loadrecords.command()
@click.argument('source', type=click.File('r'), default=sys.stdin)
@with_appcontext
def loadrecords(source):
    """Load records migration dump."""
    records = json.loads(source.read())
    create_from_json(records)
