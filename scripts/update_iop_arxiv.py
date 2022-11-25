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


def get_useful_fields():
    data = {}
    query = {
        "_source": ["control_number", "dois", "titles", "imprints"],
        "query": {
            "bool": {
                "must_not": [
                    {
                        "exists": {
                            "field": "arxiv_eprints.value"
                        }
                    }
                ],
                "must": [
                    {
                        "match": {
                            "imprints.publisher": "IOP"
                        }
                    },
                    {
                        "range": {
                            "imprints.date": {
                                "gte": "2020-01-01",
                                "lte": "2022-12-31"
                            }
                        }
                    }
                ]
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
            publisher = search_results["hits"]["hits"][record_index]["_source"]["imprints"][0]["publisher"]
            data[recid] = {'doi': doi, 'title': title, "publisher": publisher}
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


def extract_doi(element):
    doi = element.find("front/article-meta/article-id/[@pub-id-type='doi']")
    return doi.text


def extract_arxiv(element):
    arxiv = element.find(
        "front/article-meta/custom-meta-group/custom-meta/meta-value"
    )
    if arxiv is not None:
        arxiv_ = element.find("front/article-meta/article-id/[@pub-id-type='arxiv']")
        if arxiv_ is not None:
            return arxiv_.text
        return arxiv.text


def get_categories(arxiv):
    try:
        url = "https://export.arxiv.org/api/query?search_query=id:=" + arxiv
        file_content = requests.get(url).content
        element = parse_without_names_spaces(file_content)
        primary_category = element.find('entry/primary_category').get("term")
        categories_element = element.findall('entry/category')
        categories = [category.get('term')for category in categories_element]
        if primary_category not in categories:
            categories.append(primary_category)
        return categories
    except:
        return []


def get_arxiv(element, doi, title):
    arxiv = extract_arxiv(element)
    doi = extract_doi(element)
    if arxiv:
        categories = get_categories(arxiv)
        return {'arxiv': arxiv, 'categories': categories}
    arxiv_and_categories_from_api = find_arxiv_and_categories(title, doi)
    return arxiv_and_categories_from_api


def check_files(data_from_api):
    arxivs_and_dois = []
    recids = data_from_api.keys()
    for recid in recids:
        pid = PersistentIdentifier.get("recid", recid)
        existing_record = Record.get_record(pid.object_uuid)
        for file_objects in existing_record.files:
            file_path = file_objects.obj.file.uri
            with open(file_path, 'r') as f:
                file_context = f.read()
                if isXml(file_context):
                    element = parse_without_names_spaces(file_context)
                    arxiv_and_categories = get_arxiv(element, data_from_api[recid]['doi'], data_from_api[recid]['title'])
                    arxivs_and_dois.append({'doi': data_from_api[recid]['doi'], 'arxiv': arxiv_and_categories, 'recid': recid})

    return arxivs_and_dois


def isXml(value):
    try:
        ET.fromstring(value)
    except ET.ParseError:
        return False
    return True


def parse_without_names_spaces(data):
    xml = StringIO(unicode(data, "utf-8"))
    it = ET.iterparse(xml)
    for _, el in it:
        _, _, el.tag = el.tag.rpartition("}")
    root = it.root
    return root


def find_arxiv_and_categories(title, doi):
    ## https://arxiv.org/help/api/user-manual#Architecture Cannot be any doi
    url = "https://export.arxiv.org/api/query?search_query=ti:=" + title
    pattern_fir_removing_version = re.compile(r"(arxiv:|v[0-9]$)", flags=re.I)
    file_content = requests.get(url).content
    element = parse_without_names_spaces(file_content)
    try:
        entries = element.findall('entry')
        for entry in entries:
            doi = entry.find('doi')
            if doi is not None:
                if doi.text == doi:
                    arxiv = os.path.basename(element.find('entry/id').text)
                    primary_category = element.find('entry/primary_category').get("term")
                    categories_element = element.findall('category')
                    categories = [category.get('term')for category in categories_element]
                    if primary_category not in categories:
                        categories.append(primary_category)
                    arxiv = pattern_fir_removing_version.sub("", arxiv.lower())
                    return {'arxiv': arxiv, 'categories': categories}
    except Exception as e:
        print(doi, ' Crashed on ', title, e)
    pass


useful_fields = get_useful_fields()
arxiv_and_dois = check_files(useful_fields)


def update_records(recids_dois_categories):
    for item in recids_dois_categories:
        pid = PersistentIdentifier.get("recid", item['recid'])
        existing_record = Record.get_record(pid.object_uuid)
        categories = item['arxiv']['categories']
        arxiv_eprints = [
            {
                "categories": categories,
                "value": item['arxiv']['arxiv']
            }
        ]

        existing_record['arxiv_eprints'] = arxiv_eprints
        print('Updating record...', item)
        existing_record.commit()
        db.session.commit()