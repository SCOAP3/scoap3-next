import json

import requests_mock

from scoap3.cli_fixes import map_old_record, utf8rec, validate_utf8
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


def test_utf8_fix_22934_source():
    data = u'Springer/Societ\u00c3\u00a0 Italiana di Fisica'
    expected = u'Springer/Societ\xe0 Italiana di Fisica'
    assert validate_utf8(data) == (1, 0)
    assert utf8rec(data, MockRecord({})) == expected


def test_utf8_fix_22934_title():
    data = u'Status and prospects of light bino\u00e2\u0080\u0093higgsino dark matter in natural SUSY'
    expected = u'Status and prospects of light bino\u2013higgsino dark matter in natural SUSY'
    assert validate_utf8(data) == (1, 0)
    assert utf8rec(data, MockRecord({})) == expected


def test_utf8_fix_18162_abstract():
    data = u'On the other hand, LHC results for pp\u00e2\u0086\u0092e+ missing'
    expected = u'On the other hand, LHC results for pp\u2192e+ missing'
    assert validate_utf8(data) == (1, 0)
    assert utf8rec(data, MockRecord({})) == expected


def test_utf8_fix_18162_abstract_double():
    data = u'On the other hand, LHC results for pp\u00e2\u0086\u0092e+ missing'
    converted = utf8rec(data, MockRecord({}))
    assert validate_utf8(converted) == (0, 1)


def test_utf8_fix_18100_title_removed_bad():
    data = u'Search for new resonances decaying to a W or Z boson and a Higgs boson in the ' \
           u'\u00e2\u0084\u0093+\u00e2\u0084\u0093\u00e2\u0088\u0092bb\u00c2\u00af , \u00e2\u0084\u0093\u00ce\u00bdbb' \
           u'\u00c2\u00af , and \u00ce\u00bd\u00ce\u00bd\u00c2\u00afbb\u00c2\u00af channels with pp collisions at' \
           u' s=13 TeV with the ATLAS detector'
    expected = u'Search for new resonances decaying to a W or Z boson and a Higgs boson in the \u2113+\u2113\u2212bb' \
               u'\xaf , \u2113\u03bdbb\xaf , and \u03bd\u03bd\xafbb\xaf channels with pp collisions at s=13 TeV with ' \
               u'the ATLAS detector'
    assert validate_utf8(data) == (11, 0)
    assert utf8rec(data, MockRecord({})) == expected


def test_utf8_fix_18100_expected_validate():
    expected = u'Search for new resonances decaying to a W or Z boson and a Higgs boson in the \u2113+\u2113\u2212bb' \
               u'\xaf , \u2113\u03bdbb\xaf , and \u03bd\u03bd\xafbb\xaf channels with pp collisions at s=13 TeV with ' \
               u'the ATLAS detector'
    assert validate_utf8(expected) == (0, 11)


def test_utf8_fix_18100_title():
    data = u'Search for new resonances decaying to a W or Z boson and a Higgs boson in the \u00e2\u0084\u0093+' \
           u'\u00e2\u0084\u0093\u00e2\u0088\u0092bb\u00c2\u00af , \u00e2\u0084\u0093\u00ce\u00bdbb\u00c2\u00af , and ' \
           u'\u00ce\u00bd\u00ce\u00bd\u00c2\u00afbb\u00c2\u00af channels with pp collisions at s=13\u00c2 TeV with the ' \
           u'ATLAS detector'
    assert validate_utf8(data) == (11, 1)
