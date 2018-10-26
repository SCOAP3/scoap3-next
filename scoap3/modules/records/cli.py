from __future__ import absolute_import, print_function

import numbers
from HTMLParser import HTMLParser

import click
import copy
import json
import sys

from uuid import uuid1
from flask import current_app
from flask.cli import with_appcontext
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier
from invenio_records import Record
from invenio_records.models import RecordMetadata
from invenio_search import current_search_client
from invenio_workflows import WorkflowEngine
from invenio_workflows.proxies import workflow_object_class
from invenio_workflows.tasks import start
from inspire_crawler.models import CrawlerWorkflowObject
from sqlalchemy.orm.attributes import flag_modified

from scoap3.utils.google_maps import get_country


def info(msg):
    click.echo(msg)


def error(msg):
    click.echo(click.style(msg, fg='red'))


def rinfo(msg, record):
    """Helper for logging info about a record."""
    info('%s: %s' % (record.id, msg))


def rerror(msg, record):
    """Helper for logging errors about a record."""
    error('%s: %s' % (record.id, msg))


@click.group()
def loadrecords():
    """Migration commands."""


@loadrecords.command()
@click.argument('source', type=click.File('r'), default=sys.stdin)
@with_appcontext
def loadrecords(source):
    """Load records migration dump."""
    info('Loading dump...')

    records = json.loads(source.read())

    for i, record in enumerate(records['records']):
        engine = WorkflowEngine.with_name("articles_upload")
        engine.save()
        obj = workflow_object_class.create(data=record)
        obj.id_workflow = str(engine.uuid)
        extra_data = {}
        record_extra = record.pop('extra_data', {})
        if record_extra:
            extra_data['record_extra'] = record_extra

        obj.extra_data['source_data'] = {
            'data': copy.deepcopy(record),
            'extra_data': copy.deepcopy(extra_data),
        }
        obj.extra_data.update(extra_data)

        obj.data_type = current_app.config['CRAWLER_DATA_TYPE']
        obj.save()
        db.session.commit()

        job_id = uuid1()

        crawler_object = CrawlerWorkflowObject(
            job_id=job_id, object_id=obj.id
        )
        db.session.add(crawler_object)
        queue = current_app.config['CRAWLER_CELERY_QUEUE']

        start.apply_async(
            kwargs={
                'workflow_name': "articles_upload",
                'object_id': obj.id,
            },
            queue=queue,
        )

        info('Parsed record {}.'.format(i))


@click.group()
def fixdb():
    """Database fix commands."""


@fixdb.command()
@with_appcontext
@click.option('--ids', default=None, help="Comma separated list of recids to be processed. eg. '98,324'")
def unescaperecords(ids):
    """HTML unescape abstract and title for all records."""

    parser = HTMLParser()

    def proc(record, parser):
        if record.json is None:
            rerror('record.json is None', record)
            return

        unescape_abstract(record, parser)
        unescape_titles(record, parser)

    if ids:
        ids = ids.split(',')

    process_all_records(proc, 50, ids, parser)

    info('all done!')


def unescape_abstract(record, parser):
    if 'abstracts' not in record.json or len(record.json['abstracts']) == 0:
        rerror('Record has no abstracts.', record)
        return

    if len(record.json['abstracts']) > 1:
        rerror('Record has more then one abstracts (%d). Skipping.' % len(record.json['abstracts']), record)
        return

    original = record.json['abstracts'][0]['value']
    unescaped = parser.unescape(original)
    if unescaped != original:
        rinfo('Abstract changed.', record)
        record.json['abstracts'][0]['value'] = unescaped
        flag_modified(record, 'json')


def unescape_titles(record, parser):
    if 'titles' not in record.json or len(record.json['titles']) == 0:
        rerror('Record has no titles.', record)
        return

    original = record.json['titles']
    unescaped = []

    for title in original:
        if 'title' not in title:
            rerror('title key not in title', record)

        title['title'] = parser.unescape(title['title'])
        unescaped.append(title)

    if unescaped != original:
        rinfo('Authors changed.', record)
        record.json['titles'] = unescaped
        flag_modified(record, 'json')


def utf8rec(data):
    if isinstance(data, basestring):
        try:
            return ''.join(chr(ord(c)) for c in data).decode('utf8')
        except:
            return data

    if isinstance(data, tuple) or isinstance(data, list):
        return [utf8rec(element) for element in data]

    if isinstance(data, dict):
        return {k: utf8rec(v) for k, v in data.items()}

    if isinstance(data, numbers.Number) or data is None:
        return data

    error('Couldn\'t determine the data type of %s. Returning the same.' % data)
    return data


@fixdb.command()
@with_appcontext
@click.option('--ids', default=None, help="Comma separated list of recids to be processed. eg. '98,324'")
def utf8(ids):
    """Unescape records and store data as unicode."""

    def proc(record):
        if record.json is None:
            rerror('record.json is None', record)
            return
        record.json = utf8rec(record.json)
        flag_modified(record, 'json')

    if ids:
        ids = ids.split(',')

    process_all_records(proc, control_ids=ids)
    info('all done!')


@fixdb.command()
@click.option('--dry-run', is_flag=True, default=False,
              help='If set to True no changes will be committed to the database.')
@with_appcontext
def update_countries(dry_run):
    """
    Updates countries for articles, that are marked as 'HUMAN CHECK'. Countries are determined with the google maps api.
    """

    COUNTRY = "HUMAN CHECK"
    country_cache = {}
    cache_fails = 0
    total_hits = 0

    records = current_search_client.search('records-record', 'record-v1.0.0',
                                           {'size':10000, 'query': {'term': {'country': COUNTRY}}})

    info('Found %d records having %s as a country of one of the authors.' % (records['hits']['total'], COUNTRY))

    for hit in records['hits']['hits']:
        pid = PersistentIdentifier.get('recid', hit['_source']['control_number'])
        record = Record.get_record(pid.object_uuid)

        for author_index, author_data in enumerate(record['authors']):
            for aff_index, aff_data in enumerate(author_data['affiliations']):
                if aff_data['country'] == COUNTRY:
                    total_hits += 1

                    # cache countries based on old affiliation value to decrease api requests
                    old_value = aff_data['value']
                    if old_value not in country_cache:
                        country_cache[old_value] = get_country(old_value)
                        cache_fails += 1

                    new_country = country_cache[old_value]

                    if new_country:
                        record['authors'][author_index]['affiliations'][aff_index]['country'] = new_country
                        info('Changed country for record with id %s to %s' % (record['control_number'], new_country))
                    else:
                        error('Could not find country for record with id %s' % record['control_number'])

        if not dry_run:
            record.commit()
            db.session.commit()

    info('In total %d countries needed to be updated and %d queries were made to determine the countries.' % (total_hits, cache_fails))

    if dry_run:
        error('NO CHANGES were committed to the database, because --dry-run flag was present.')


def process_all_records(function, chuck_size=50, control_ids=(), *args):
    """
    Calls the 'function' for all records.
    If 'control_ids' is set to a non empty list, then only those records will be processed.
    :param function: Function to be called for all record. First parameter will be a RecordMetadata object.
    :param chuck_size: How many records should be queried at once from db.
    :param control_ids: Control ids of records. If set to a non empty list, this will be used to filter records
    :param args: Args to be passed to 'function'
    """
    info('gathering records...')

    # query ids from all records
    record_ids = RecordMetadata.query.with_entities(RecordMetadata.id)

    # filter records
    if control_ids:
        info('applying filter for records...')
        uuids = [PersistentIdentifier.get('recid', recid).object_uuid for recid in control_ids]
        record_ids = record_ids.filter(RecordMetadata.id.in_(uuids))

    # get record ids
    record_ids = [r[0] for r in record_ids.all()]
    records_count = len(record_ids)
    processed = 0

    info('start processing %d records...' % records_count)

    # process record chunks
    for i in range((records_count / chuck_size) + 1):
        # calculate chunk start and end position
        ixn = i * chuck_size
        current_ids = record_ids[ixn:ixn+chuck_size]

        # process current chunk
        for record in RecordMetadata.query.filter(RecordMetadata.id.in_(current_ids)):
            try:
                function(record, *args)
            except Exception as e:
                raise  # TODO Should we handle anything here, or just stop the whole process?
            processed += 1

        # commiting processed precords
        info('partial commit...')
        db.session.commit()

        info('%s records processed.' % processed)

    # have we processed everything?
    assert(processed == records_count)
