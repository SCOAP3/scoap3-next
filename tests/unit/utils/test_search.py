from scoap3.modules.search.utils import Scoap3RecordsSearch


def test_escape_query_string():
    data = {
        'query': {
            'query_string': {
                'query': '10.1016/j.nuclphysb.2018.07.004'
            }
        }
    }
    Scoap3RecordsSearch.escape_query_string(data)
    assert data['query']['query_string']['query'] == '10.1016\\/j.nuclphysb.2018.07.004'


def test_escape_query_string_empty():
    data = {}
    Scoap3RecordsSearch.escape_query_string(data)
    assert data == {}
