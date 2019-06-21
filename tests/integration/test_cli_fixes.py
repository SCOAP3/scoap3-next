import requests_mock
from mock import patch

from scoap3.cli_fixes import process_record_for_publication_date_fix
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
