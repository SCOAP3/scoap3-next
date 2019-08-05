from mock import patch

from scoap3.modules.compliance.compliance import _arxiv, _files
from scoap3.modules.compliance.models import Compliance
from tests.unit.test_records import MockApp


def test_status_change_false():
    c = Compliance()
    c.results = {
        'accepted': False,
    }
    c.history = []

    assert c.has_final_result_changed() is True


def test_status_change_true():
    c = Compliance()
    c.results = {
        'accepted': True,
    }
    c.history = []

    assert c.has_final_result_changed() is True


def test_status_change_history_false():
    c = Compliance()
    c.results = {
        'accepted': False,
    }
    c.history = [
        {'results': {'accepted': False}}
    ]

    assert c.has_final_result_changed() is False


def test_status_change_history_true():
    c = Compliance()
    c.results = {
        'accepted': True,
    }
    c.history = [
        {'results': {'accepted': False}}
    ]

    assert c.has_final_result_changed() is True


def base_test_arxiv(record):
    config = {
        'ARXIV_HEP_CATEGORIES': ['hep-ph'],
        'ARTICLE_CHECK_HAS_TO_BE_HEP': ['Advances in High Energy Physics', 'Physical Review C'],
    }

    with patch('scoap3.modules.compliance.compliance.current_app', MockApp(config)):
        return _arxiv(record, None)


def test_arxiv():
    record = {
        "arxiv_eprints": [
            {
                "categories": [
                    "hep-ph",
                    "nucl-th"
                ],
                "value": "1903.12380"
            }
        ],
        "publication_info": [
            {
                "journal_title": "Physical Review C",
            }
        ],
    }

    assert base_test_arxiv(record) == (True, ('Primary category: hep-ph', ), None)


def test_arxiv_wrong_category():
    record = {
        "arxiv_eprints": [
            {
                "categories": [
                    "physics.ins-det",
                    "hep-ph"
                ],
                "value": "1709.01064"
            }
        ],
        "publication_info": [
            {
                "journal_title": "Advances in High Energy Physics",
            }
        ],
    }

    assert base_test_arxiv(record) == (False, ('Primary category: physics.ins-det', ), None)


def test_arxiv_wrong_category_dont_care_journal():
    record = {
        "arxiv_eprints": [
            {
                "categories": [
                    "physics.ins-det",
                    "hep-ex"
                ],
                "value": "1902.04655"
            }
        ],
        "publication_info": [
            {
                "journal_title": "European Physical Journal C"
            }
        ]
    }

    assert base_test_arxiv(record) == (True, ("Doesn't have to be hep", ), None)


def base_test_files(record):
    config = {
        'COMPLIANCE_JOURNAL_FILES': {
            'European Physical Journal C': {'xml', 'pdf/a'},
        }
    }

    with patch('scoap3.modules.compliance.compliance.current_app', MockApp(config)):
        return _files(record, None)


def test_files():
    record = {
        "_files": [{"filetype": "xml"}, {"filetype": "pdf/a"}],
        "publication_info": [{"journal_title": "European Physical Journal C"}]
    }

    assert base_test_files(record) == (True, [], None)


def test_files_missing():
    record = {
        "_files": [{"filetype": "pdf/a"}],
        "publication_info": [{"journal_title": "European Physical Journal C"}]
    }

    assert base_test_files(record) == (False, ['Missing files: xml'], None)


def test_files_extra():
    record = {
        "_files": [{"filetype": "xml"}, {"filetype": "pdf/a"}, {"filetype": "extra"}],
        "publication_info": [{"journal_title": "European Physical Journal C"}]
    }

    assert base_test_files(record) == (False, ['Extra files: extra'], None)


def test_files_no_files():
    record = {
        "publication_info": [{"journal_title": "European Physical Journal C"}]
    }

    assert base_test_files(record) == (False, ['Missing files: xml, pdf/a'], None)
