from invenio_search import current_search_client as es
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_files.api import Record
import os
from io import StringIO
import re
import xml.etree.ElementTree as ET
import requests
import sys
reload(sys)
sys.setdefaultencoding('utf8')
from invenio_db import db

def update_arxiv_manually():
    dois = {"10.1088/1674-1137/ac90af" :"2202.13741",
        "10.1088/1674-1137/ac8bc9" :"2204.13249",
        "10.1088/1674-1137/ac930b" :"2205.03942",
        "10.1088/1674-1137/ac92da" :"2109.11754",
        "10.1088/1674-1137/ac89d1" :"2207.02043",
        "10.1088/1674-1137/ac8789" :"1903.09388",
        "10.1088/1674-1137/ac89d0" :"2204.05418",
        "10.1088/1674-1137/ac87f1" :"2207.03126",
        "10.1088/1674-1137/ac878c" :"2206.06547",
        "10.1088/1674-1137/ac745a" :"2203.14730",
        "10.1088/1674-1137/ac7547" :"2112.02519",
        "10.1088/1674-1137/ac6e35" :"2201.00517",
        "10.1088/1674-1137/ac6e37" :"2201.12998",
        "10.1088/1674-1137/ac68da" :"2008.07116",
        "10.1088/1674-1137/ac6666" :"2111.08901",
        "10.1088/1674-1137/ac62ca" :"2203.16500",
        "10.1088/1674-1137/ac600c" :"2212.11861",
        "10.1088/1674-1137/ac4cb5" :"2201.06881",
        "10.1088/1674-1137/ac567e" :"2202.00904",
        "10.1088/1674-1137/ac425a" :"2002.12218",
        "10.1088/1674-1137/ac4694" :"2108.12207",
        "10.1088/1674-1137/ac338e" :"2011.10987"}
    data= {}
    for doi in dois.keys():
        query = {
            "_source": ["control_number", "dois", "titles"],
            "query": {
                "bool": {
                    "must": [{"match": {"dois.value": doi}}],
                }
            }
        }
        search_results = es.search(index="scoap3-records-record", scroll='1m', body=query)
        sid = search_results['_scroll_id']
        scroll_size = len(search_results['hits']['hits'])
        while (scroll_size > 0):
            for record_index in range(scroll_size):
                recid = search_results["hits"]["hits"][record_index]["_source"]["control_number"]
                doi = search_results["hits"]["hits"][record_index]["_source"]["dois"][0]["value"]
                title = search_results["hits"]["hits"][record_index]["_source"]["titles"][0]["title"]
                data[recid] = {'doi': doi, 'arxiv': dois[doi], "title": title}
            search_results = es.scroll(scroll_id=sid, scroll='2m')
            sid = search_results['_scroll_id']
            scroll_size = len(search_results['hits']['hits'])
    return data

def parse_without_names_spaces(data):
    xml = StringIO(unicode(data, "utf-8"))
    it = ET.iterparse(xml)
    for _, el in it:
        _, _, el.tag = el.tag.rpartition("}")
    root = it.root
    return root

def get_categories(arxiv):
    # try:
        url = "https://export.arxiv.org/api/query?search_query=id:=" + arxiv
        file_content = requests.get(url).content
        element = parse_without_names_spaces(file_content)
        primary_category = element.find('entry/primary_category').get("term")
        categories_element = element.findall('entry/category')
        categories = [category.get('term')for category in categories_element]
        print(categories)
        if primary_category not in categories:
            categories.append(primary_category)
        return categories
    # except:
    #     return []

def join_categories_and_arxiv(data):
    recids = data.keys()
    records_with_categories = data
    for recid in recids:
        categories = get_categories(data[recid]['arxiv'])
        records_with_categories[recid]['categories'] = categories
        print(records_with_categories[recid])
    return records_with_categories

def update_records(data):
    recids = data.keys()
    for recid in recids:
        pid = PersistentIdentifier.get("recid", recid)
        existing_record = Record.get_record(pid.object_uuid)
        arxiv_eprints = [
            {
                "categories": data[recid]['categories'],
                "value": data[recid]['arxiv']
            }
        ]
        existing_record['arxiv_eprints'] = arxiv_eprints
        existing_record.update(dict(existing_record))
        print('Updating record...', arxiv_eprints)
        existing_record.commit()
        db.session.commit()

data = update_arxiv_manually()
final = join_categories_and_arxiv(data)
update_records(final)

