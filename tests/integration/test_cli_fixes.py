import requests_mock
from invenio_pidstore.models import PersistentIdentifier
from invenio_records.models import RecordMetadata
from mock import patch

from scoap3.cli_fixes import process_record_for_publication_date_fix, change_oai_hostname_for_record
from tests.responses import read_response


class MockRecord:
    id = None

    def __init__(self, json):
        self.json = json


def test_fix_publication_date():
    with requests_mock.Mocker() as m, \
            patch('scoap3.cli_fixes.flag_modified'):
        m.get('https://api.crossref.org/works/10.1103/PhysRevD.99.075025',
              content=read_response('article_upload', 'crossref.org_works_10.1103_PhysRevD.99.075025'))

        record_data = {
            'dois': [{'value': '10.1103/PhysRevD.99.075025'}],
            'imprints': [{'date': '2000-01-01'}]
        }
        record = MockRecord(record_data)
        process_record_for_publication_date_fix(record, 2, False)

        assert record_data['imprints'][0]['date'] == '2019-04-25'


def test_fix_publication_date_dry_run():
    with requests_mock.Mocker() as m, \
            patch('scoap3.cli_fixes.flag_modified'):
        m.get('https://api.crossref.org/works/10.1103/PhysRevD.99.075025',
              content=read_response('article_upload', 'crossref.org_works_10.1103_PhysRevD.99.075025'))

        record_data = {
            'dois': [{'value': '10.1103/PhysRevD.99.075025'}],
            'imprints': [{'date': '2000-01-01'}]
        }
        record = MockRecord(record_data)
        process_record_for_publication_date_fix(record, 2, True)

        assert record_data['imprints'][0]['date'] == '2000-01-01'


def test_fix_publication_date_small_diff():
    with requests_mock.Mocker() as m, \
            patch('scoap3.cli_fixes.flag_modified'):
        m.get('https://api.crossref.org/works/10.1103/PhysRevD.99.075025',
              content=read_response('article_upload', 'crossref.org_works_10.1103_PhysRevD.99.075025'))

        record_data = {
            'dois': [{'value': '10.1103/PhysRevD.99.075025'}],
            'imprints': [{'date': '2019-04-24'}]
        }
        record = MockRecord(record_data)
        process_record_for_publication_date_fix(record, 2, False)

        assert record_data['imprints'][0]['date'] == '2019-04-24'


def test_change_oai_hostname_for_record(app_client, test_record):
    assert 'control_number' in test_record
    control_number = test_record['control_number']

    assert 'id' in test_record.get('_oai', {})

    old_identifier = test_record['_oai']['id']
    new_identifier = '%s.newtest' % old_identifier
    response = app_client.get('/oai2d?verb=GetRecord&metadataPrefix=marc21&identifier=%s' % old_identifier)
    assert response.status_code == 200

    response = app_client.get('/oai2d?verb=GetRecord&metadataPrefix=marc21&identifier=%s' % new_identifier)
    assert response.status_code == 422

    pid = PersistentIdentifier.get('recid', control_number)
    test_record = RecordMetadata.query.get(pid.object_uuid)
    change_oai_hostname_for_record(test_record, old_identifier, new_identifier, False)

    response = app_client.get('/oai2d?verb=GetRecord&metadataPrefix=marc21&identifier=%s' % old_identifier)
    assert response.status_code == 422

    response = app_client.get('/oai2d?verb=GetRecord&metadataPrefix=marc21&identifier=%s' % new_identifier)
    assert response.status_code == 200


def test_change_oai_hostname_for_record_dry_run(app_client, test_record):
    assert 'control_number' in test_record
    control_number = test_record['control_number']

    assert 'id' in test_record.get('_oai', {})

    old_identifier = test_record['_oai']['id']
    new_identifier = '%s.newtest' % old_identifier
    response = app_client.get('/oai2d?verb=GetRecord&metadataPrefix=marc21&identifier=%s' % old_identifier)
    assert response.status_code == 200

    response = app_client.get('/oai2d?verb=GetRecord&metadataPrefix=marc21&identifier=%s' % new_identifier)
    assert response.status_code == 422

    pid = PersistentIdentifier.get('recid', control_number)
    test_record = RecordMetadata.query.get(pid.object_uuid)
    change_oai_hostname_for_record(test_record, old_identifier, new_identifier, True)

    response = app_client.get('/oai2d?verb=GetRecord&metadataPrefix=marc21&identifier=%s' % old_identifier)
    assert response.status_code == 200

    response = app_client.get('/oai2d?verb=GetRecord&metadataPrefix=marc21&identifier=%s' % new_identifier)
    assert response.status_code == 422
