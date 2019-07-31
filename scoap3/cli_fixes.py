import numbers

import click
from dateutil.parser import parse as parse_date
from flask import current_app
from flask.cli import with_appcontext
from invenio_db import db
from invenio_files_rest.models import Location
from invenio_pidstore.models import PersistentIdentifier
from sqlalchemy.orm.attributes import flag_modified

from scoap3.utils.nations import find_country
from scoap3.utils.click_logging import rerror, error, info, rinfo
from scoap3.utils.crossref import parse_date_parts
from scoap3.utils.http import requests_retry_session
from scoap3.utils.processor import process_all_records


@click.group()
def fixdb():
    """Database fix commands."""


def validate_utf8(data):
    """
    This function checks how many occurrences of "normal" utf8 characters are in the given string (ie. unconvertible)
    and how many convertible occurrences.

    There are cases, when a UTF8 character got "double encoded", i.e. its bytes were separately encoded.
    This resulted in encodings like:
      - "\u00c3\u00a0" instead of "\xe0"
      - "\u00e2\u0080\u0093" istead of "\u2013", etc.

    Returns an (convertible_count, unconvertible_count) tuple.
    """
    convertible_count = 0
    unconvertible_count = 0

    needed_bytes = 0
    for char in data:
        char_int = ord(char)
        char_binary = format(char_int, '08b')
        if needed_bytes:
            if char_int <= 255 and char_binary[:2] == '10':
                needed_bytes -= 1
                if needed_bytes == 0:
                    convertible_count += 1
                continue
            else:
                needed_bytes = 0
                unconvertible_count += 1

        if char_int > 255:  # surely not convertible
            unconvertible_count += 1
        elif char_binary[0] == '0':
            # standard ascii char
            pass
        elif char_binary[:3] == '110':
            needed_bytes = 1
        elif char_binary[:4] == '1110':
            needed_bytes = 2
        elif char_binary[:5] == '11110':
            needed_bytes = 3
        else:
            # other proper utf8 character
            unconvertible_count += 1

    return convertible_count, unconvertible_count


def utf8rec(data, record):
    if isinstance(data, basestring):
        convertible_count, unconvertible_count = validate_utf8(data)
        if convertible_count > 0:
            if unconvertible_count == 0:
                rinfo('converted "%s"' % (data[:50]), record)
                return ''.join(chr(ord(c)) for c in data).decode('utf8')
            else:
                rerror('both convertible (%d) and unconvertible (%d) values are present in "%s"' %
                       (convertible_count, unconvertible_count, data[:50]), record)

        return data

    if isinstance(data, tuple) or isinstance(data, list):
        return [utf8rec(element, record) for element in data]

    if isinstance(data, dict):
        return {k: utf8rec(v, record) for k, v in data.items()}

    if isinstance(data, numbers.Number) or data is None:
        return data

    rerror('Couldn\'t determine the data type of %s. Returning the same.' % data, record)
    return data


@fixdb.command()
@with_appcontext
@click.option('--ids', default=None, help="Comma separated list of recids to be processed. eg. '98,324'")
@click.option('--dry-run', is_flag=True, default=False,
              help='If set to True no changes will be committed to the database.')
def utf8(ids, dry_run):
    """Unescape records and store data as unicode."""

    def proc(record):
        if record.json is None:
            rinfo('record.json is None', record)
            return

        try:
            new_json = utf8rec(record.json, record)
            if record.json != new_json and not dry_run:
                record.json = new_json
                flag_modified(record, 'json')
        except (UnicodeDecodeError, ValueError) as e:
            rerror(u'failed: %s' % e, record)

    if ids:
        ids = ids.split(',')

    process_all_records(proc, control_ids=ids)

    if dry_run:
        error('NO CHANGES were committed to the database, because --dry-run flag was present.')

    info('all done!')


@fixdb.command()
@click.option('--dry-run', is_flag=True, default=False,
              help='If set to True no changes will be committed to the database.')
@click.option('--ids', default=None, help="Comma separated list of recids to be processed. eg. '98,324'")
@with_appcontext
def update_countries(dry_run, ids):
    """
    Updates countries for articles, that are marked as given parameter. Countries are determined with the google maps api.
    """

    counts = {'changed': 0, 'all': 0}

    if ids:
        ids = ids.split(',')

    def proc(record):
        try:
            if 'authors' not in record.json:
                error('no authors for record %s' % record.json['control_number'])
                return

            for author_index, author_data in enumerate(record.json['authors']):
                if 'affiliations' not in author_data:
                    error('no affiliations for record %s' % record.json['control_number'])
                    continue

                for aff_index, aff_data in enumerate(author_data['affiliations']):
                    counts['all'] += 1

                    new_country = find_country(aff_data['value'])
                    if aff_data['country'] != new_country:
                        counts['changed'] += 1

                        info('Changed country for record with id %s from %s to %s' % (record.json['control_number'],
                                                                                      aff_data['country'], new_country))
                        record.json['authors'][author_index]['affiliations'][aff_index]['country'] = new_country

            if not dry_run:
                flag_modified(record, 'json')
        except Exception as e:
            error(str(e))

    process_all_records(proc, control_ids=ids)

    if dry_run:
        error('NO CHANGES were committed to the database, because --dry-run flag was present.')

    info("%s\nDONE." % counts)


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


def process_record_for_publication_date_fix(record, min_day_diff, dry_run):
    """
    Processes all records and checks the difference between crossref dates and the imprints.date field.
    If the difference is bigger then `min_day_diff`, then it will override the date stored.
    """

    crossref_url = current_app.config.get('CROSSREF_API_URL')

    if record.json:
        doi = record.json['dois'][0]['value']
        api_response = requests_retry_session().get(crossref_url + doi)

        if api_response.status_code != 200:
            rerror('api response %d' % api_response.status_code, record)
            return

        api_message = api_response.json()['message']
        if 'published-online' in api_message:
            cross_date = parse_date_parts(api_message['published-online']['date-parts'][0])
        else:
            cross_date = parse_date_parts(api_message['created']['date-parts'][0])

        pub_date = parse_date(record.json['imprints'][0]['date'])

        diff_days = abs((pub_date-cross_date).days)

        rinfo('diff: %d' % diff_days, record)
        if diff_days >= min_day_diff:
            formatted_cross_date = cross_date.date().isoformat()
            rinfo('replaced: %s -> %s' % (record.json['imprints'][0]['date'], formatted_cross_date), record)

            # only save changes if not a dry_run
            if not dry_run:
                record.json['imprints'][0]['date'] = formatted_cross_date
                flag_modified(record, 'json')


@fixdb.command()
@with_appcontext
@click.option('--dry-run', is_flag=True, default=False,
              help='If set to True no changes will be committed to the database.')
@click.option('--ids', default=None, help="Comma separated list of recids to be processed. eg. '98,324'.")
@click.option('--min_day_diff', default=2, help="Minimum day difference when replace will take place.")
def fix_publication_date(dry_run, ids, min_day_diff):
    """
    Processes all records and checks the difference between crossref dates and the imprints.date field.
    If the difference is bigger then `min_day_diff`, then it will override the date stored.
    """

    if ids:
        ids = ids.split(',')

    process_all_records(process_record_for_publication_date_fix, 50, ids, min_day_diff, dry_run)

    info('ALL DONE!')

    if dry_run:
        error('NO CHANGES were committed to the database, because --dry-run flag was present.')


def change_oai_hostname_for_record(record, old_hostname, new_hostname, dry_run):
    if not record.json:
        rerror('no json', record)
        return

    if 'id' not in record.json.get('_oai', {}):
        rerror('no oai information', record)
        return

    pid = PersistentIdentifier.query\
        .filter(PersistentIdentifier.object_uuid == record.id)\
        .filter(PersistentIdentifier.pid_type == 'oai').one_or_none()

    if not pid:
        rerror('no pid found', record)
        return

    if old_hostname in pid.pid_value:
        new_pid_value = pid.pid_value.replace(old_hostname, new_hostname)

        rinfo('%s -> %s' % (pid.pid_value, new_pid_value), record)

        if not dry_run:
            pid.pid_value = new_pid_value
            record.json['_oai']['id'] = new_pid_value
            flag_modified(record, 'json')
    else:
        rinfo('old_hosname not found in pid_value (%s)' % pid.pid_value, record)


@fixdb.command()
@with_appcontext
@click.option('--dry-run', is_flag=True, default=False,
              help='If set to True no changes will be committed to the database.')
@click.option('--ids', default=None, help="Comma separated list of recids to be processed. eg. '98,324'.")
@click.argument('old_hostname')
@click.argument('new_hostname')
def change_oai_hostname(dry_run, ids, old_hostname, new_hostname):
    """Changes the hostname part of all OAI-PMH identifier."""

    if ids:
        ids = ids.split(',')

    process_all_records(change_oai_hostname_for_record, 50, ids, old_hostname, new_hostname, dry_run)

    info('ALL DONE!')

    if dry_run:
        error('NO CHANGES were committed to the database, because --dry-run flag was present.')


@fixdb.command()
@with_appcontext
@click.option('--dry-run', is_flag=True, default=False,
              help='If set to True no changes will be committed to the database.')
@click.option('--ids', default=None, help="Comma separated list of recids to be processed. eg. '98,324'.")
def change_schema_url(dry_run, ids):
    def proc(record):
        schema_key = '$schema'
        new_schema = 'http://repo.scoap3.org/schemas/hep.json'

        if not record.json:
            rerror('no json', record)
            return

        old_schema = record.json.get(schema_key, '')
        if old_schema != new_schema:
            rinfo('%s -> %s' % (old_schema, new_schema), record)

            if not dry_run:
                record.json[schema_key] = new_schema
                flag_modified(record, 'json')

    if ids:
        ids = ids.split(',')

    process_all_records(proc, 50, ids)

    info('ALL DONE!')

    if dry_run:
        error('NO CHANGES were committed to the database, because --dry-run flag was present.')
