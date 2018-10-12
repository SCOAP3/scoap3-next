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
from invenio_records.models import RecordMetadata
from invenio_workflows import WorkflowEngine
from invenio_workflows.proxies import workflow_object_class
from invenio_workflows.tasks import start
from inspire_crawler.models import CrawlerWorkflowObject
from sqlalchemy.orm.attributes import flag_modified


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
def unescaperecords():
    """HTML unescape abstract and title for all records."""

    parser = HTMLParser()

    def proc(record, parser):
        if record.json is None:
            rerror('record.json is None', record)
            return

        unescape_abstract(record, parser)
        unescape_titles(record, parser)

    process_all_records(proc, 50, parser)

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
def utf8():
    """Unescape records and store data as unicode."""

    def proc(record):
        if record.json is None:
            rerror('record.json is None', record)
            return
        record.json = utf8rec(record.json)
        flag_modified(record, 'json')

    process_all_records(proc)
    info('all done!')


def process_all_records(function, chuck_size=50, *args):
    info('gathering records...')

    # query ids from all records
    record_ids = RecordMetadata.query.with_entities(RecordMetadata.id).all()
    record_ids = [r[0] for r in record_ids]
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