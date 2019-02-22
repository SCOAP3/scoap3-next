from os import path

import requests_mock

from scoap3.utils.arxiv import get_arxiv_categories, clean_arxiv
from tests.responses import get_response_dir


def test_categories():
    """Test extraction arxiv categories from arxiv api."""

    file_path = path.join(get_response_dir(), 'arxiv', '1811.00370.xml')
    with open(file_path, 'rb') as f:
        file_data = f.read()

        with requests_mock.Mocker() as m:
            m.get('http://export.arxiv.org/api/query?search_query=id:1811.00370', text=file_data)
            categories = get_arxiv_categories('1811.00370')
            assert categories == ['hep-th', 'gr-qc', 'math-ph', 'math.MP']


def test_clean_arxiv():
    """Test getting clean arXiv identifier."""

    data = (
        ('arxiv:12356.78', '12356.78'),
        ('arXiv:12356.78v2', '12356.78'),
        ('12356.78', '12356.78'),
        ('arXiv:hep-th/0401244', 'hep-th/0401244'),
    )

    for arxiv, clean_arxiv_id in data:
        assert clean_arxiv(arxiv) == clean_arxiv_id
