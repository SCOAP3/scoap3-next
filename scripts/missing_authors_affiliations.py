from invenio_search import current_search_client as es
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_files.api import Record
from invenio_db import db
import re


def get_no_affiliations():
    records = {}
    query = {
        "_source": ["_files", "control_number", "dois"],
        "query": {
            "bool": {
                "must_not": [
                    {
                        "exists": {
                            "field": "authors.affiliations"
                        }
                    },
                ]
            }
        }
    }


    search_result = es.search(index="scoap3-records-record", scroll='1m', body=query)
    sid = search_result['_scroll_id']
    scroll_size = len(search_result['hits']['hits'])
    while (scroll_size > 0):
        for record_index in range(scroll_size):
            recid = search_result["hits"]["hits"][record_index]["_source"]["control_number"]
            doi = search_result["hits"]["hits"][record_index]["_source"]["dois"][0]["value"]
            records[recid] = doi
        search_result = es.scroll(scroll_id=sid, scroll='2m')
        sid = search_result['_scroll_id']
        scroll_size = len(search_result['hits']['hits'])
    return records
