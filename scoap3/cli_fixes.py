import click
from flask.cli import with_appcontext
from invenio_db import db
from invenio_files_rest.models import Location

from scoap3.utils.click_logging import error


@click.group()
def fixdb():
    """Database fix commands."""


@fixdb.command()
@with_appcontext
def init_default_location():
    """
    Add default Location, if not already present.
    Used by Travis as well.
    """

    if not Location.query.filter(Location.name == 'default').count():
        loc = Location()
        loc.name = 'default'
        loc.default = True
        loc.uri = '/virtualenv/files/'
        db.session.add(loc)
        db.session.commit()
    else:
        error("Default location already exists.")
