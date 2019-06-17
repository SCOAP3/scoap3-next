from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records import Record
from pytest import raises
from sqlalchemy.orm.exc import NoResultFound


def test_record_deletion(test_record):
    recid = test_record.get('control_number')
    assert recid

    test_record.delete()
    db.session.commit()

    pid = PersistentIdentifier.get('recid', recid)
    assert pid.status == PIDStatus.DELETED

    with raises(NoResultFound):
        Record.get_record(pid.object_uuid)
