from elasticsearch import NotFoundError
from flask import current_app
from flask_sqlalchemy import models_committed
from inspire_utils.record import get_value
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_indexer.signals import before_record_index
from invenio_pidstore.models import PersistentIdentifier
from invenio_records import Record
from invenio_records.models import RecordMetadata
from invenio_records.signals import after_record_delete


@before_record_index.connect
def enchance_before_index(sender, json, *args, **kwargs):
    """Enchance record data for indexing"""

    publication_date = get_value(json, 'imprints[0].date')
    if publication_date:
        json['year'] = publication_date[:4]


@models_committed.connect
def index_after_commit(sender, changes):
    """Index records automatically after each modification."""

    indexer = RecordIndexer()
    for model_instance, change in changes:
        if isinstance(model_instance, RecordMetadata):
            if change in ('insert', 'update') and model_instance.json:
                indexer.index(Record(model_instance.json, model_instance))
            else:
                try:
                    indexer.delete(Record(model_instance.json, model_instance))
                except NotFoundError:
                    # Record not found in ES
                    current_app.logger.warning('Record with id "%s" not found in ElasticSearch' %
                                               model_instance.json.get('control_number'))


@after_record_delete.connect
def delete_pid_after_record_deletion(sender, record):
    pid = PersistentIdentifier.get_by_object('recid', 'rec', record.id)
    pid.delete()
    db.session.commit()
