from mock import patch

from scoap3.modules.tools.tools import affiliations_export
from tests.responses import read_response_as_json
from tests.unit.test_records import MockApp


class MockES:
    def __init__(self, search_result, **kwargs):
        self.kwargs = kwargs
        self.search_result = search_result

    def search(self, **kwargs):
        assert kwargs == self.kwargs
        return self.search_result


def base_test_affiliation(country):
    search_index = 'scoap3-records-record'
    search_result = read_response_as_json('elasticsearch', 'tool_affiliations.json')
    q = 'country:%s' % country if country else None
    kwargs = {
        'q': q,
        'index': search_index,
        '_source': [
            'publication_info.year', 'publication_info.journal_title', 'arxiv_eprints', 'dois',
            'authors', 'control_number',
        ],
        'size': 100,
        'from_': 0
    }
    es = MockES(search_result, **kwargs)

    config = {'SEARCH_UI_SEARCH_INDEX': search_index}

    with patch('scoap3.modules.tools.tools.current_search_client', es), \
            patch('scoap3.modules.tools.tools.current_app', MockApp(config)):
        return affiliations_export(country=country)


def test_affiliation_export():
    expected_result = read_response_as_json('tools', 'affiliation_expected.json')
    result = base_test_affiliation(country=None)
    assert result['data'] == expected_result


def test_affiliation_export_country():
    expected_result = read_response_as_json('tools', 'affiliation_expected_us.json')
    result = base_test_affiliation(country='USA')
    assert result['data'] == expected_result
