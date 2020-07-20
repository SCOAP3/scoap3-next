import os
import json

import click
from flask.cli import with_appcontext
from invenio_db import db
from invenio_files_rest.models import Location
from invenio_records.api import Record
from invenio_search import current_search_client


from scoap3.utils.click_logging import error, info


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
        loc.uri = os.environ.get('SCOAP_DEFAULT_LOCATION') or '/virtualenv/files/'
        db.session.add(loc)
        db.session.commit()
    else:
        error("Default location already exists.")


@fixdb.command()
@click.option(
    '--dry-run',
    is_flag=True,
    default=False,
    help='If set to True no changes will be committed to the database.')
@click.argument(
    'json_file',
    type=click.Path(exists=True))
@with_appcontext
def fix_doi_dates(json_file, dry_run):
    """
    Fixes the imprint/publication/copyright dates on a list of DOIs.
    """
    with open(json_file) as _file:
        dois_with_dates = json.load(_file)

    for doi in dois_with_dates.keys():
        search_result = current_search_client.search(
            'scoap3-records',
            q='dois.value:"{}"'.format(doi)
        )['hits']['hits']

        if search_result:
            uuid = search_result[0]['_id']
            rec = Record.get_record(uuid)

            date = dois_with_dates[doi]
            year = int(date.split('-')[0])
            old_date = rec['imprints'][0]['date']

            rec['imprints'][0]['date'] = date
            rec['publication_info'][0]['year'] = year
            rec['copyright'][0]['year'] = year

            info('DOI {} with UUID {}: changed {} -> {}'
                 .format(doi, uuid, old_date, date))

            if not dry_run:
                rec.commit()
                db.session.commit()
                info('{} successfully updated.'.format(doi))

        else:
            error('DOI {} not found in ES.'.format(doi))

    if dry_run:
        error('NO CHANGES were committed to the database, because --dry-run flag was present.')
