import json

import requests_mock

from scoap3.cli_fixes import map_old_record
from tests.responses import read_hep_schema, read_titles_schema, read_response


class MockRecord:
    id = None

    def __init__(self, json):
        self.json = json


def run_mapper_with_mock(record, mock_address, dry_run=True):
    mock_address.register_uri('GET', '/schemas/hep.json', content=read_hep_schema())
    mock_address.register_uri('GET', '/schemas/elements/titles.json', content=read_titles_schema())

    return map_old_record(MockRecord(record), dry_run)


def test_map_old_record_ptep():
    with requests_mock.Mocker() as mock_address:
        mock_address.register_uri('GET', 'http://export.arxiv.org/api/query?search_query=id:1308.1535',
                                  content=read_response('arxiv', '1308.1535'))
        data = json.loads(read_response('cli_fixes', 'test_map_old_record_ptep.json'))
        expected_data = json.loads(read_response('cli_fixes', 'test_map_old_record_ptep_expected.json'))
        assert run_mapper_with_mock(data, mock_address).json == expected_data


def test_map_old_record_elsevier():
    with requests_mock.Mocker() as mock_address:
        data = json.loads(read_response('cli_fixes', 'test_map_old_record_elsevier.json'))
        expected_data = json.loads(read_response('cli_fixes', 'test_map_old_record_elsevier_expected.json'))

        assert run_mapper_with_mock(data, mock_address).json == expected_data


def test_map_old_record_SISSA():
    with requests_mock.Mocker() as mock_address:
        mock_address.register_uri('GET', 'http://export.arxiv.org/api/query?search_query=id:1309.3748',
                                  content=read_response('arxiv', '1309.3748'))
        data = json.loads(read_response('cli_fixes', 'test_map_old_record_sissa.json'))
        expected_data = json.loads(read_response('cli_fixes', 'test_map_old_record_sissa_expected.json'))

        assert run_mapper_with_mock(data, mock_address).json == expected_data


def test_map_old_record_jagiellonian():
    with requests_mock.Mocker() as mock_address:
        mock_address.register_uri('GET', 'http://export.arxiv.org/api/query?search_query=id:1501.04446',
                                  content=read_response('arxiv', '1501.04446'))
        data = json.loads(read_response('cli_fixes', 'test_map_old_record_jagiellonian.json'))
        expected_data = json.loads(read_response('cli_fixes', 'test_map_old_record_jagiellonian_expected.json'))

        assert run_mapper_with_mock(data, mock_address).json == expected_data


def test_map_old_record_broken_report_numbers():
    """Both report_numbers and arxiv_eprints fields are present."""
    with requests_mock.Mocker() as mock_address:
        data = json.loads(read_response('cli_fixes', 'test_map_old_record_broken_report_numbers.json'))

        assert run_mapper_with_mock(data, mock_address) is None


def test_map_old_record_none():
    with requests_mock.Mocker() as mock_address:
        assert run_mapper_with_mock(None, mock_address) is None


def test_map_old_record_remove_arxiv_prefix():
    with requests_mock.Mocker() as mock_address:
        data = json.loads(read_response('cli_fixes', 'test_map_old_record_remove_arxiv_prefix.json'))
        expected_data = json.loads(read_response('cli_fixes', 'test_map_old_record_remove_arxiv_prefix_expected.json'))

        assert run_mapper_with_mock(data, mock_address).json == expected_data


def test_map_old_record_hindawi():
    with requests_mock.Mocker() as mock_address:
        mock_address.register_uri('GET', 'http://export.arxiv.org/api/query?search_query=id:1803.07709',
                                  content=read_response('arxiv', '1803.07709'))
        data = json.loads(read_response('cli_fixes', 'test_map_old_record_hindawi.json'))
        expected_data = json.loads(read_response('cli_fixes', 'test_map_old_record_hindawi_expected.json'))

        assert run_mapper_with_mock(data, mock_address).json == expected_data


def test_map_old_record_springer():
    with requests_mock.Mocker() as mock_address:
        data = json.loads(read_response('cli_fixes', 'test_map_old_record_springer.json'))
        expected_data = json.loads(read_response('cli_fixes', 'test_map_old_record_springer_expected.json'))

        assert run_mapper_with_mock(data, mock_address).json == expected_data


def test_map_old_record_acquisition_date():
    with requests_mock.Mocker() as mock_address:
        mock_address.register_uri('GET', 'http://export.arxiv.org/api/query?search_query=id:1511.03024',
                                  content=read_response('arxiv', '1511.03024'))
        data = json.loads(read_response('cli_fixes', 'test_map_old_record_acquisition_date.json'))
        expected_data = json.loads(read_response('cli_fixes', 'test_map_old_record_acquisition_date_expected.json'))

        assert run_mapper_with_mock(data, mock_address).json == expected_data


def test_map_old_record_orcid_prefix():
    with requests_mock.Mocker() as mock_address:
        data = json.loads(read_response('cli_fixes', 'test_map_old_record_orcid_prefix.json'))
        expected_data = json.loads(read_response('cli_fixes', 'test_map_old_record_orcid_prefix_expected.json'))

        assert run_mapper_with_mock(data, mock_address).json == expected_data


def test_map_old_record_empty_author_prop():
    with requests_mock.Mocker() as mock_address:
        data = json.loads(read_response('cli_fixes', 'test_map_old_record_empty_author_prop.json'))
        expected_data = json.loads(read_response('cli_fixes', 'test_map_old_record_empty_author_prop_expected.json'))

        assert run_mapper_with_mock(data, mock_address).json == expected_data
