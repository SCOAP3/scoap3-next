from mock import patch

from scoap3.modules.tools.tools import affiliations_export, authors_export, search_export
from tests.responses import read_response_as_json
from tests.unit.test_records import MockApp


class MockES:
    def __init__(self, search_result, with_assert=True, **kwargs):
        self.kwargs = kwargs
        self.search_result = search_result
        self.with_assert = with_assert

    def search(self, **kwargs):
        if self.with_assert:
            assert kwargs == self.kwargs

        return self.search_result


def base_test_tool(export_function, country):
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
        return export_function(country=country)


def test_affiliation_export():
    expected_result = read_response_as_json('tools', 'affiliation_expected.json')
    result = base_test_tool(export_function=affiliations_export, country=None)
    assert result['data'] == expected_result


def test_affiliation_export_country():
    expected_result = read_response_as_json('tools', 'affiliation_expected_us.json')
    result = base_test_tool(export_function=affiliations_export, country='USA')
    assert result['data'] == expected_result


def test_author_export():
    expected_result = read_response_as_json('tools', 'authors_expected.json')
    result = base_test_tool(export_function=authors_export, country=None)
    assert result['data'] == expected_result


def test_search_export():
    expected_result = read_response_as_json('tools', 'search_expected.json')

    search_index = 'scoap3-records-record'
    search_result = read_response_as_json('elasticsearch', 'tool_search.json')
    es = MockES(search_result, with_assert=False)

    config = {
        'SEARCH_UI_SEARCH_INDEX': search_index,
        'SEARCH_EXPORT_FIELDS': (
            ('Publication year', 'year', 'year'),
            ('Control number', 'control_number', 'control_number'),
            ('DOI', 'dois', 'dois[0].value'),
            ('Title', 'titles', 'titles[0].title'),
            ('arXiv id', 'arxiv_eprints', 'arxiv_eprints[0].value'),
            ('arXiv primary category', 'arxiv_eprints', 'arxiv_eprints[0].categories[0]'),
            ('Publication date', 'imprints', 'imprints[0].date'),
            ('Record creation date', 'record_creation_date', 'record_creation_date'),
            ('Journal', 'publication_info', 'publication_info[0].journal_title'),
        )
    }

    with patch('scoap3.modules.tools.tools.current_search_client', es), \
            patch('scoap3.modules.tools.tools.current_app', MockApp(config)):
        result = search_export(None)
        assert result['data'] == expected_result
