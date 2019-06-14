import requests_mock

from scoap3.utils.inspire import get_inspire_arxiv_categories_for_record
from tests.responses import read_response


def test_category():
    with requests_mock.Mocker() as m:
        m.get('https://labs.inspirehep.net/api/literature?q=doi:10.1103/physrevd.99.114502',
              text=read_response('inspire', '10.1103_physrevd.99.114502.json'))

        assert get_inspire_arxiv_categories_for_record('doi:10.1103/physrevd.99.114502') == ["hep-lat", "hep-ph"]


def test_category_empty_response():
    with requests_mock.Mocker() as m:
        m.get('https://labs.inspirehep.net/api/literature?q=doi:not_found.json',
              text=read_response('inspire', 'not_found.json'))

        assert get_inspire_arxiv_categories_for_record('doi:not_found.json') is None
