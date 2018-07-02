from flask_cli import with_appcontext

from dojson.contrib.marc21.utils import create_record, split_stream
from jsonschema.exceptions import ValidationError
from scoap3.dojson.hep.model import hep
from invenio_records import Record
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.errors import PIDAlreadyExists
from scoap3.modules.pidstore.minters import scoap3_recid_minter
from flask import url_for

from invenio_workflows.proxies import workflow_object_class

import click
import sys

@click.group()
def loadrecords():
    """Migration commands."""


@loadrecords.command()
@click.argument('source', type=click.File('r'), default=sys.stdin)
@with_appcontext
def loadrecords(source):
    """Load records migration dump."""
    click.echo('Loading dump...')

    for i, data in enumerate(split_stream(source),):
        record = hep.do(create_record(data))
        print("Creating record {} with recid: {}".format(i, create_record(data)['001']))
        record['$schema'] = url_for('invenio_jsonschemas.get_schema', schema_path="hep.json")
        del record['self']

        obj = workflow_object_class.create(data=record)
        extra_data = {
            'recid': obj['recid']
        }
        record_extra = obj.pop('extra_data', {})
        if record_extra:
            extra_data['record_extra'] = record_extra

        obj.extra_data['source_data'] = {
            'data': copy.deepcopy(obj),
            'extra_data': copy.deepcopy(extra_data),
        }
        obj.extra_data.update(extra_data)

        obj.data_type = current_app.config['CRAWLER_DATA_TYPE']
        obj.save()
        db.session.commit()

        crawler_object = CrawlerWorkflowObject(
            job_id=uuid, object_id=obj.id
        )
        db.session.add(crawler_object)
        queue = current_app.config['CRAWLER_CELERY_QUEUE']

        if record_error is None:
            start.apply_async(
                kwargs={
                    'workflow_name': 'articles_upload',
                    'object_id': obj.id,
                },
                queue=queue,
            )

        current_app.logger.info('Parsed {} records.'.format(len(results_data)))

        # try:
        #     record = Record.create(obj, id_=None)
        # except ValidationError as err:
        #     print("Validation error: %s. Skipping..." % (err,))

        # # Create persistent identifier.
        # try:
        #     pid = scoap3_recid_minter(str(record.id), record)
        # except PIDAlreadyExists:
        #     print("Alredy in DB")
        #     continue

        # # Commit any changes to record
        # record.commit()

        # # Commit to DB before indexing
        # db.session.commit()

        # # Index record
        # indexer = RecordIndexer()
        # indexer.index_by_id(pid.object_uuid)


