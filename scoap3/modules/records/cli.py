from __future__ import absolute_import, print_function

import click
import json
import sys

from flask.cli import with_appcontext
from invenio_records.cli import records

from scoap3.modules.records.tasks import perform_article_check
from scoap3.modules.records.util import create_from_json


@records.command()
@click.option('--from_date', help='Date to start the check from in YYYY-mm-dd format.')
@with_appcontext
def crossref_diff(from_date):
    perform_article_check(from_date)


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
