from scoap3.modules.compliance.compliance import _unique_arXiv


def test_unique_arxiv_no_arxiv_id():
    record = {
        "publication_info": [
            {
                "journal_title": "European Physical Journal C"
            }
        ]
    }
    assert _unique_arXiv(record, None) == (True, ('No arXiv id: Out of the scope of this check', ), None)


def test_unique_arxiv_where_arxiv_does_not_exist():
    record = {
        "arxiv_eprints": [
            {
                "categories": [
                    "physics.ins-det",
                    "hep-ex"
                ],
                "value": "12453456"
            }
        ],
        "publication_info": [
            {
                "journal_title": "European Physical Journal C"
            }
        ]
    }
    assert _unique_arXiv(record, None) == (True, ('ArXiv ID not found. Unique ID.', ), None)
