#1
from invenio_files_rest.models import ObjectVersion
from zipfile import ZipFile
from invenio_search import current_search_client as es
from invenio_db import db
from io import StringIO
import xml.etree.ElementTree as ET
from zipfile import ZipFile
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_files.api import Record
import os
import re


def find_all_records_that_have_files():
    query = {
        "query": {
            "bool": {
                "must": [{"exists": {"field": "_files"}}],
            }
        }
    }

    search_result = es.search(index="scoap3-records-record", scroll='1m', body=query)
    sid = search_result['_scroll_id']
    scroll_size = len(search_result['hits']['hits'])
    paths_and_dois = {}
    f = open("files_paths.txt", "w")
    while (scroll_size > 0):
        for record_index in range(scroll_size):
            doi = search_result["hits"]["hits"][record_index]["_source"]["dois"][0]["value"]
            publisher = search_result["hits"]["hits"][record_index]["_source"]["imprints"][0]["publisher"]
            creation_date = search_result["hits"]["hits"][record_index]["_source"]["_created"]
            update_date = search_result["hits"]["hits"][record_index]["_source"]["_updated"]
            recid = search_result["hits"]["hits"][record_index]["_source"]["control_number"]
            paths = find_files_paths(search_result["hits"]["hits"][record_index])
            if paths:
                for path in paths:
                    f.write((path['path'] + " " + path['file_type'] + " " + doi + " " + publisher + " " + update_date + " " + creation_date + "\n").encode('utf-8'))
                    paths_and_dois[doi] = path
        search_result = es.scroll(scroll_id=sid, scroll='2m')
        sid = search_result['_scroll_id']
        scroll_size = len(search_result['hits']['hits'])
    f.close()
    return paths_and_dois

def find_files_paths(search_result):
    paths = []
    try:
        files = [pdfa for pdfa in search_result["_source"]["_files"]]
        for file in files:
            path = ObjectVersion.get(file['bucket'], file['key']).file.uri
            file_type = file['filetype']
            paths.append({'path': path, 'file_type': file_type})
        return paths
    except:
        pass

### Later awk
# awk '{split($0, a, " "); if (system("[ -f \"" a[1] "\" ]") != 0) print $0 > "missing_files.txt"}' files_paths.txt
