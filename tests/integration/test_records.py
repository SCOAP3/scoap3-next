from datetime import date
from freezegun import freeze_time
import requests_mock
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records import Record
from mock import patch
from pytest import raises
from sqlalchemy.orm.exc import NoResultFound

from scoap3.modules.records.tasks import perform_article_check_for_journal
from tests.responses import read_response


def test_record_deletion(test_record):
    recid = test_record.get('control_number')
    assert recid

    test_record.delete()
    db.session.commit()

    pid = PersistentIdentifier.get('recid', recid)
    assert pid.status == PIDStatus.DELETED

    with raises(NoResultFound):
        Record.get_record(pid.object_uuid)


def test_article_check():
    from_date = date(2019, 6, 21)
    journal = 'Physical Review D'
    cooperation_dates = (None, None)

    with requests_mock.Mocker() as m, \
            patch('scoap3.modules.records.tasks.is_doi_in_db', return_value=False), \
            freeze_time('2019-06-24'):

        m.get('https://api.crossref.org/works/?filter=from-pub-date%3A2019-06-21%2Ccontainer-title%3APhysical+Review+D'
              '&cursor=%2A', text=read_response('crossref', 'PRD_list_partial.json'))
        m.get('https://api.crossref.org/works/?filter=from-pub-date%3A2019-06-21%2Ccontainer-title%3APhysical+Review+D'
              '&cursor=AoJynOylvesCPw1odHRwOi8vZHguZG9pLm9yZy8xMC4xMTAzL3BoeXNyZXZkLjk5LjEyMzAxNw%3D%3D',
              text=read_response('crossref', 'PRD_list_partial_2.json'))
        m.get('https://labs.inspirehep.net/api/literature?q=doi%3A10.1103%2Fphysrevd.99.125011',
              text=read_response('inspire', '10.1103_physrevd.99.125011.json'))
        m.get('https://labs.inspirehep.net/api/literature?q=doi%3A10.1103%2Fphysrevd.99.123525',
              text=read_response('inspire', '10.1103_physrevd.99.123525.json'))

        journal_stats, missing_records = perform_article_check_for_journal(from_date, journal, cooperation_dates)
        assert journal_stats == {'outside_cooperation_dates': 0, 'missing': 1, 'journal': 'Physical Review D',
                                 'in_db': 0, 'no_arxiv_category': 0, 'non_hep_arxiv_category': 1}
        assert missing_records == [
            ('10.1103/physrevd.99.125011', 'Extensivity, entropy current, area law, and Unruh effect')
        ]
