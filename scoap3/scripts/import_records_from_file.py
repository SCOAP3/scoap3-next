from dojson.contrib.marc21.utils import create_record, split_stream
from scoap3.hep.model import hep
from invenio_records import Record
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from scoap3.modules.pidstore.minters import scoap3_recid_minter

recs = [hep.do(create_record(data)) for data in split_stream(open('../data/scoap3export.xml', 'r'))]

for i, obj in enumerate(recs, start=1):
    print("Creating record {}/{}".format(i, len(recs)))
    record = Record.create(data, id_=None)
    print record

    # Create persistent identifier.
    pid = scoap3_recid_minter(str(record.id), record)
    print(pid.object_uuid)

    # Commit any changes to record
    record.commit()

    # Commit to DB before indexing
    db.session.commit()

    # Index record
    indexer = RecordIndexer()
    indexer.index_by_id(pid.object_uuid)
