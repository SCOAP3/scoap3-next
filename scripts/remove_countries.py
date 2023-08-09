from invenio_search import current_search_client as es
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_files.api import Record
from invenio_db import db
import re


def get_cern_cooperation_agreement():
    recids = []
    query = {
        "_source": ["_files", "control_number","authors" ],
        "query": {
            "regexp": {
                "authors.affiliations.value": {
                    "value": ".*cooperation.*",
                    "flags": "ALL",
                    "case_insensitive": "true",
                }
                }
            }
        }

    search_result = es.search(index="scoap3-records-record", scroll='1m', body=query)
    sid = search_result['_scroll_id']
    scroll_size = len(search_result['hits']['hits'])
    while (scroll_size > 0):
        for record_index in range(scroll_size):
            recid = search_result["hits"]["hits"][record_index]["_source"]["control_number"]
            for author in search_result["hits"]["hits"][record_index]["_source"].get("authors", []):
                for affiliation in author.get("affiliations", []):
                    pattern_for_cern_cooperation_agreement = re.compile(r'cooperation agreement with cern', re.IGNORECASE)
                    match_pattern = pattern_for_cern_cooperation_agreement.search(affiliation.get("value", ""))
                    if match_pattern:
                        if "country" in affiliation:
                            if recid not in recids:
                                recids.append(recid)
        search_result = es.scroll(scroll_id=sid, scroll='2m')
        sid = search_result['_scroll_id']
        scroll_size = len(search_result['hits']['hits'])
    return recids

def remove_country(record):
    for author in record["authors"]:
        for affiliation in author.get('affiliations', []):
            pattern_for_cern_cooperation_agreement = re.compile(r'cooperation agreement with cern', re.IGNORECASE)
            match_pattern = pattern_for_cern_cooperation_agreement.search(affiliation.get("value", ""))
            if match_pattern is not None:
                affiliation.pop('country', None)
    return record

def update_records(recids):
    for recid in recids:
        pid = PersistentIdentifier.get("recid", recid)
        existing_record = Record.get_record(pid.object_uuid)
        existing_record = remove_country(existing_record)
        existing_record.update(dict(existing_record))
        print('Updating record...', recid)
        existing_record.commit()
        db.session.commit()


records_with_wrong_aff = get_cern_cooperation_agreement()
updated_ = update_records(records_with_wrong_aff)