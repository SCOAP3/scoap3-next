from invenio_search import current_search_client as es
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_files.api import Record
from invenio_db import db
import re


def get_cern_cooperation_agreement():
    records = {}
    query = {
        "_source": ["_files", "control_number", "dois"],
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
            doi = search_result["hits"]["hits"][record_index]["_source"]["dois"][0]["value"]
            records[recid] = doi
        search_result = es.scroll(scroll_id=sid, scroll='2m')
        sid = search_result['_scroll_id']
        scroll_size = len(search_result['hits']['hits'])
    return records

def remove_country(record):
    for author in record["authors"]:
        try:
            for affiliation in author["affiliations"]:
                pattern_for_cern_cooperation_agreement = re.compile(r'cooperation agreement with cern', re.IGNORECASE)
                match_pattern = pattern_for_cern_cooperation_agreement.search(affiliation["value"])
                if match_pattern is not None:
                    affiliation.pop("country")
        except KeyError:
            print("Author has no affiliations", record['control_number'])
    return record

def update_records(data):
    recids = data.keys()
    updated_records = {}
    for recid in recids:
        pid = PersistentIdentifier.get("recid", recid)
        existing_record = Record.get_record(pid.object_uuid)
        existing_record = remove_country(existing_record)
        existing_record.update(dict(existing_record))
        updated_records[recid] = existing_record
        print('Updating record...', recid)
        existing_record.commit()
        db.session.commit()
    return updated_records


records_with_wrong_aff = get_cern_cooperation_agreement()
updated_records = update_records(records_with_wrong_aff)