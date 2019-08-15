from __future__ import absolute_import, print_function

import click
from flask.cli import with_appcontext
import json
import sys
from StringIO import StringIO

from invenio_db import db
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_records.cli import records
from invenio_records_files.api import Record as APIRecord
from invenio_pidstore.models import PersistentIdentifier
from sqlalchemy.orm.exc import NoResultFound

from scoap3.utils.click_logging import error, info
from scoap3.utils.http import requests_retry_session
from scoap3.modules.records.tasks import perform_article_check
from scoap3.modules.records.util import create_from_json


@records.command()
@click.option('--from_date', help='Date to start the check from in YYYY-mm-dd format.')
@with_appcontext
def crossref_diff(from_date):
    perform_article_check(from_date)


@records.command()
@click.option('--control-number', help='Control number of the record to attached the new file to.', required=True)
@click.option('--file-path', help='Path to the file. Either local path, or starting with http:// or https://.',
              required=True)
@click.option('--file-type', help='General options: pdf, pdf/a, xml', required=True)
@click.option('--filename', help='The file name will be used as a key for the file, i.e. if the key already exists'
                                 'for the record, the file will be overwritten.', required=True)
@with_appcontext
def attach_file(control_number, file_path, file_type, filename):
    """
    Attach a file to an already existing record.

    The file-path can point to a local file, but also http and https protocols are supported. For these protocols
    sending specific headers are not supported, so make sure the website doesn't require any.

    In case the record already has a file with the given filename, it will be overwritten.
    """

    # get existing record
    try:
        api_record = APIRecord.get_record(PersistentIdentifier.get('recid', control_number).object_uuid)
    except (PIDDoesNotExistError, NoResultFound):
        error('No record found for given control number!')
        return

    # read and attach file
    if file_path.startswith('http://') or file_path.startswith('https://'):
        data = requests_retry_session().get(file_path)
        if data.status_code != 200:
            error('Could not download file. Status code: %d' % data.status_code)
            return

        file_data = StringIO(data.content)
        api_record.files[filename] = file_data
        api_record.files[filename]['filetype'] = file_type
    else:
        try:
            with open(file_path) as f:
                api_record.files[filename] = f
                api_record.files[filename]['filetype'] = file_type
        except IOError:
            error('local file was not found or not readable: %s' % file_path)
            return

    api_record.commit()
    db.session.commit()
    info('File successfully attached.')


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
