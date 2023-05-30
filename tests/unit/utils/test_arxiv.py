import requests_mock
from pytest import raises, mark
import requests

from scoap3.utils.arxiv import get_arxiv_categories, clean_arxiv
from tests.responses import read_response


def test_categories():
    """Test extraction arXiv categories from arXiv api."""

    file_data = read_response('arxiv', '1811.00370.xml')

    with requests_mock.Mocker() as m:
        m.get('http://export.arxiv.org/api/query?search_query=id:1811.00370', text=file_data)
        categories = get_arxiv_categories('1811.00370')
        assert categories == ['hep-th', 'gr-qc', 'math-ph', 'math.MP']


def test_empty_response():
    """Test extraction arXiv categories from arXiv api."""

    file_data = read_response('arxiv', 'empty.xml')

    with requests_mock.Mocker() as m:
        m.get('http://export.arxiv.org/api/query?search_query=id:not_found', text=file_data)
        categories = get_arxiv_categories('not_found')
        assert categories == []


def test_ambiguous_title():
    """Test for receiving more then one result for partial title."""
    title = 'hep'

    arxiv_search_title_hep = read_response('arxiv', 'search_title_hep.xml')
    with requests_mock.Mocker() as m:
        m.get('http://export.arxiv.org/api/query?search_query=ti:"%s"' % title, text=arxiv_search_title_hep)
        categories = get_arxiv_categories(title=title)
        assert categories == []


def test_extract_arxiv_id():
    """Test getting clean arXiv identifier."""
    assert clean_arxiv('12356.78') == '12356.78'


def test_extract_arxiv_id_version():
    """Test getting clean arXiv identifier."""
    assert clean_arxiv('arXiv:12356.78v2') == '12356.78'


def test_extract_arxiv_id_prefix():
    """Test getting clean arXiv identifier."""
    assert clean_arxiv('arxiv:12356.78') == '12356.78'


def test_extract_arxiv_id_complex():
    """Test getting clean arXiv identifier."""
    assert clean_arxiv('arXiv:hep-th/0401244') == 'hep-th/0401244'


def test_extract_arxiv_none():
    """Test for None param."""
    assert clean_arxiv(None) is None


def test_extract_arxiv_with_categ():
    """
    Test for arxiv with category.
    Delivered for article: 10.1140/epjc/s10052-019-6679-6
    """
    assert clean_arxiv('arXiv:1803.07217 [gr-qc]') == '1803.07217'

@mark.vcr
def test_categories_with_arxiv():
    """Test extraction arXiv categories from arXiv api."""
    categories =  get_arxiv_categories(arxiv_id='2111.13053', title="Axial Chiral Vortical Effect in a Sphere with finite size effect", doi="10.1088/1674-1137/acac6d")
    assert categories == ['hep-th']

@mark.vcr
def test_categories_without_arxiv_just_title():
    """Test extraction arXiv categories from arXiv api."""
    categories = get_arxiv_categories(title="Static properties and Semileptonic transitions of lowest-lying double heavy baryons")
    assert categories == ['hep-ph']

@mark.vcr
def test_categories_without_arxiv_just_doi():
    """Test extraction arXiv categories from arXiv api."""
    categories = get_arxiv_categories(doi="10.1088/1674-1137/acac6c")
    assert categories == []

@mark.vcr
def test_categories_without_arxiv_with_title_and_doi():
    """Test extraction arXiv categories from arXiv api."""
    categories = get_arxiv_categories(doi="10.1088/1674-1137/acac6c", title="Static properties and Semileptonic transitions of lowest-lying double heavy baryons")
    assert categories == ['hep-ph']

@mark.vcr
def test_categories_with_arxiv_type_unicode():
    """Test extraction arXiv categories from arXiv api."""
    categories =  get_arxiv_categories(arxiv_id=u'2111.13053', title="Axial Chiral Vortical Effect in a Sphere with finite size effect", doi="10.1088/1674-1137/acac6d")
    assert categories == ['hep-th']
