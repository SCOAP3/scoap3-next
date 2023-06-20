import os
from zipfile import ZipFile
import re
from invenio_search import current_search_client as es
from io import StringIO
import xml.etree.ElementTree as ET
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_files.api import Record
from invenio_db import db


def find_articles_recid():
    dois_and_recids = {}
    dois = ["10.1103/PhysRevD.97.072005",
        "10.1103/PhysRevD.97.032001",
        "10.1103/PhysRevD.97.051102",
        "10.1103/PhysRevD.98.012005",
        "10.1103/PhysRevLett.121.052003",
        "10.1103/PhysRevLett.121.062001",
        "10.1103/PhysRevLett.121.031801",
        "10.1103/PhysRevD.98.072001",
        "10.1103/PhysRevD.98.071101",
        "10.1103/PhysRevLett.121.232001",
        "10.1103/PhysRevD.98.091102",
        "10.1103/PhysRevD.97.012004",
        "10.1103/PhysRevD.97.011101",
        "10.1103/PhysRevD.97.012005",
        "10.1103/PhysRevD.99.071102",
        "10.1103/PhysRevD.99.111101",
        "10.1103/PhysRevD.99.112006",
        "10.1103/PhysRevD.100.011101",
        "10.1103/PhysRevD.100.012001",
        "10.1103/PhysRevD.100.012002",
        "10.1103/PhysRevD.100.092008",
        "10.1103/PhysRevD.100.112010",
        "10.1103/PhysRevD.100.111103",
        "10.1103/PhysRevD.101.032007",
        "10.1103/PhysRevD.101.052012",
        "10.1103/PhysRevLett.124.141801",
        "10.1103/PhysRevLett.124.161803",
        "10.1103/PhysRevD.101.091101",
        "10.1103/PhysRevD.102.012003",
        "10.1103/PhysRevLett.125.161806",
        "10.1103/PhysRevD.102.071102",
        "10.1103/PhysRevD.102.071103",
        "10.1103/PhysRevD.102.092011",
        "10.1103/PhysRevD.102.112001",
        "10.1103/PhysRevD.102.111101",
        "10.1103/PhysRevD.100.032006",
        "10.1103/PhysRevLett.122.011801",
        "10.1103/PhysRevD.99.032003",
        "10.1103/PhysRevD.100.031101",
        "10.1103/PhysRevD.99.031102",
        "10.1103/PhysRevD.99.011102",
        "10.1103/PhysRevD.98.092015",
        "10.1103/PhysRevD.98.112006",
        "10.1103/PhysRevD.98.112008",
        "10.1103/PhysRevD.98.112016",
        "10.1103/PhysRevLett.122.082001",
        "10.1103/PhysRevD.99.011104",
        "10.1103/PhysRevLett.122.042001",
        "10.1103/PhysRevD.103.032003",
        "10.1103/PhysRevD.100.052007",
        "10.1103/PhysRevD.103.052005",
        "10.1103/PhysRevLett.126.122001",
        "10.1103/PhysRevD.103.052013",
        "10.1103/PhysRevLett.126.161801",
        "10.1103/PhysRevD.103.072004",
        "10.1103/PhysRevD.103.112005",
        "10.1103/PhysRevD.104.052003",
        "10.1103/PhysRevLett.127.121803",
        "10.1103/PhysRevD.103.L111101",
        "10.1103/PhysRevD.104.012008",
        "10.1103/PhysRevD.104.012007",
        "10.1103/PhysRevD.103.112001",
        "10.1103/PhysRevD.104.012012",
        "10.1103/PhysRevD.99.032012",
        "10.1103/PhysRevLett.122.072501",
        "10.1103/PhysRevD.104.052005",
        "10.1103/PhysRevD.104.072008",
        "10.1103/PhysRevLett.127.181802",
        "10.1103/PhysRevD.105.072007",
        "10.1103/PhysRevLett.128.142005",
        "10.1103/PhysRevD.105.L091101",
        "10.1103/PhysRevD.105.L011102",
        "10.1103/PhysRevD.105.012007",
        "10.1103/PhysRevD.105.012003",
        "10.1103/PhysRevD.105.012004",
        "10.1103/PhysRevD.105.032002",
        "10.1103/PhysRevD.105.L051101",
        "10.1103/PhysRevD.104.112006",
        "10.1103/PhysRevLett.127.261801",
        "10.1103/PhysRevD.104.112011",
        "10.1103/PhysRevD.104.L091105",
        "10.1103/PhysRevLett.128.081804",
        "10.1103/PhysRevD.106.012003",
        "10.1103/PhysRevD.106.012006",
        "10.1103/PhysRevD.106.L051103",
        "10.1103/PhysRevD.106.032013",
        "10.1103/PhysRevD.102.012002"]

    for doi in dois:
        query = {
            "query": {
                "bool": {
                    "must": [{"match": {"dois.value": doi}}],
                }
            }
        }
        search_result = es.search(index="scoap3-records-record", body=query)
        try:
            recid = recid = search_result["hits"]["hits"][0]["_source"]["control_number"]
            dois_and_recids[recid] = doi
        except:
            pass
    return dois_and_recids

def update_records(dois_and_recids):
    recids = dois_and_recids.keys()
    for recid in recids[1:]:
        pid = PersistentIdentifier.get("recid", recid)
        existing_record = Record.get_record(pid.object_uuid)
        for index_auth, author in enumerate(existing_record['authors']):
            for index_aff, affiliation in enumerate(existing_record['authors'][index_auth]['affiliations']):
                if "University of Sydney, New South Wales" in affiliation['value']:
                    print("Country is " + existing_record['authors'][index_auth]['affiliations'][index_aff]['country'])
                    existing_record['authors'][index_auth]['affiliations'][index_aff]['country'] = "Australia"
                    print("Country should be " + existing_record['authors'][index_auth]['affiliations'][index_aff]['country'])
                else:
                    pass
        print('Updating record...', recid)
        existing_record.update(dict(existing_record))
        existing_record.commit()
        db.session.commit()

data = find_articles_recid()
update_records(data)


