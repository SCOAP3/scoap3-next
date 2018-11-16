from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier
from invenio_records.models import RecordMetadata

from scoap3.modules.analysis.models import ArticlesImpact
from scoap3.utils.click_logging import info


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
        current_ids = record_ids[ixn:ixn + chuck_size]

        # process current chunk
        for record in RecordMetadata.query.filter(RecordMetadata.id.in_(current_ids)):
            try:
                function(record, *args)
            except Exception:
                raise  # TODO Should we handle anything here, or just stop the whole process?
            processed += 1

        # commiting processed precords
        info('partial commit...')
        db.session.commit()

        info('%s records processed.' % processed)

    # have we processed everything?
    assert (processed == records_count)


def process_all_articles_impact(function, chuck_size=50, *args):
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
    record_ids = ArticlesImpact.query.with_entities(ArticlesImpact.control_number)

    # get record ids
    record_ids = [r[0] for r in record_ids.all()]
    records_count = len(record_ids)
    processed = 0
    info('start processing %d records...' % records_count)

    # process record chunks
    for i in range((records_count // chuck_size) + 1):
        # calculate chunk start and end position
        ixn = i * chuck_size
        current_ids = record_ids[ixn:ixn + chuck_size]

        # process current chunk
        for record in ArticlesImpact.query.filter(ArticlesImpact.control_number.in_(current_ids)):
            try:
                function(record, *args)
            except Exception:
                raise  # TODO Should we handle anything here, or just stop the whole process?
            processed += 1

        # commiting processed precords
        info('partial commit...')
        db.session.commit()

        info('%s records processed.' % processed)

    # have we processed everything?
    assert (processed == records_count)
