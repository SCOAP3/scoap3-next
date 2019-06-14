import requests_mock

from scoap3.utils.crossref import get_crossref_items
from tests.responses import read_response


def test_crossref_items():
    filter_param = 'from-created-date:2019-06-01,container-title:Physical Review C'

    response_1 = read_response('crossref', 'works_list_1.json')
    response_2 = read_response('crossref', 'works_list_2.json')
    response_3 = read_response('crossref', 'works_list_3.json')
    cursor_1 = '*'
    cursor_2 = 'AoJ/6e7QoesCPw1odHRwOi8vZHguZG9pLm9yZy8xMC4xMTAzL3BoeXNyZXZjLjk5LjA2MTMwMQ=='
    cursor_3 = 'AoJ9lfqGpOsCPw1odHRwOi8vZHguZG9pLm9yZy8xMC4xMTAzL3BoeXNyZXZjLjk5LjA2NTIwMQ=='
    with requests_mock.Mocker() as m:
        mock_base_url = '//api.crossref.org/works/?filter=%s&cursor=%s'
        mock_url_1 = mock_base_url % (filter_param, cursor_1)
        mock_url_2 = mock_base_url % (filter_param, cursor_2)
        mock_url_3 = mock_base_url % (filter_param, cursor_3)
        m.get(mock_url_1, text=response_1)
        m.get(mock_url_2, text=response_2)
        m.get(mock_url_3, text=response_3)

        dois = [e['DOI'] for e in get_crossref_items(filter_param)]

        assert dois == [
            "10.1103/physrevc.99.064304", "10.1103/physrevc.99.064303", "10.1103/physrevc.99.064601",
            "10.1103/physrevc.99.064301", "10.1103/physrevc.99.064302", "10.1103/physrevc.99.064305",
            "10.1103/physrevc.99.064306", "10.1103/physrevc.99.065801", "10.1103/physrevc.99.064901",
            "10.1103/physrevc.99.064603", "10.1103/physrevc.99.065802", "10.1103/physrevc.99.064902",
            "10.1103/physrevc.99.064602", "10.1103/physrevc.99.064308", "10.1103/physrevc.99.064307",
            "10.1103/physrevc.99.064311", "10.1103/physrevc.99.065804", "10.1103/physrevc.99.065501",
            "10.1103/physrevc.99.064310", "10.1103/physrevc.99.061301", "10.1103/physrevc.99.064312",
            "10.1103/physrevc.99.064607", "10.1103/physrevc.99.064606", "10.1103/physrevc.99.064605",
            "10.1103/physrevc.99.064309", "10.1103/physrevc.99.065803", "10.1103/physrevc.99.064604",
            "10.1103/physrevc.99.064314", "10.1103/physrevc.99.064313", "10.1103/physrevc.99.065201",
        ]
