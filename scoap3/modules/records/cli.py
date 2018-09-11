from __future__ import absolute_import, print_function

import click
import copy
import json
import sys

from uuid import uuid1
from flask import current_app
from flask.cli import with_appcontext
from invenio_db import db
from invenio_workflows import WorkflowEngine
from invenio_workflows.proxies import workflow_object_class
from invenio_workflows.tasks import start
from inspire_crawler.models import CrawlerWorkflowObject


@click.group()
def loadrecords():
    """Migration commands."""


@loadrecords.command()
@click.argument('source', type=click.File('r'), default=sys.stdin)
@with_appcontext
def loadrecords(source):
    """Load records migration dump."""
    click.echo('Loading dump...')

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

        click.echo('Parsed record {}.'.format(i))
