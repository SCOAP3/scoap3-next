from invenio_search import current_search_client as es
from invenio_records_files.api import Record
import os
from io import StringIO
from zipfile import ZipFile
import re
import xml.etree.ElementTree as ET


def get_all_IOP_articles_dois_without_arxiv():
    dois = []
    query = {
        "size": 100,
        "query": {
            "bool": {
                "must_not": {
                    "exists": {
                        "field": "arxiv_eprints.value"
                    }
                }
            },
            "bool": {
                "must": [{"match": {"imprints.publisher": "IOP"}}],
            },
            "bool": {
                "must": {
                    "range": {"imprints.date": {"gte": "2020-01-01", "lte": "2022-12-31"}}
                }
            }
        }
    }
    search_results = es.search(index="scoap3-records-record", scroll='1m', body=query)
    sid = search_results['_scroll_id']
    scroll_size = len(search_results['hits']['hits'])
    while (scroll_size > 0):
        for record_index in range(scroll_size):
            try:
                doi = search_results["hits"]["hits"][record_index]["_source"]["dois"]
                dois = dois + [doi_['value'] for doi_ in doi]
            except:
                pass
            search_results = es.scroll(scroll_id=sid, scroll='2m')
            sid = search_results['_scroll_id']
            scroll_size = len(search_results['hits']['hits'])
    return dois


def get_arxivs_and_dois(dois):
    import sys
    reload(sys)
    sys.setdefaultencoding('utf8')

    path = "/data/harvesting/IOP/download/"
    arxivs = {}
    zips = [os.path.join(path, zip_file) for zip_file in os.listdir(path) if '.zip' in zip_file]
    for zip_file in zips:
        with ZipFile(zip_file, 'r') as zip:
            name = os.path.basename(zip_file).split('.')[0]
            all_files_names_in_zip = zip.namelist()
            for file_name in all_files_names_in_zip:
                if 'xml' in file_name:
                    data = zip.read(file_name)
                    element = parse_without_names_spaces(data)
                    doi = get_doi(element)
                    if doi in dois:
                        arxivs[doi] = get_arxiv(element)
                    else:
                        query = {
                            "query": {
                                "bool": {
                                    "must": [{"match": {"dois.value": doi}}],
                                }
                            }
                        }
                        search_result = es.search(index="scoap3-records-record", body=query)
                        try:
                            recid = search_result["hits"]["hits"][0]["_source"]["control_number"]
                        except:
                            print("No record with doi ", doi )
    return arxivs


def parse_without_names_spaces(data):
    xml = StringIO(unicode(data, "utf-8"))
    it = ET.iterparse(xml)
    for _, el in it:
        _, _, el.tag = el.tag.rpartition("}")
    root = it.root
    return root


def get_doi(element):
    doi = element.find("front/article-meta/article-id/[@pub-id-type='doi']")
    return doi.text


def get_arxiv(element):
    arxiv = element.find(
        "front/article-meta/custom-meta-group/custom-meta/meta-value"
    )
    if arxiv is not None:
        return arxiv.text


dois = get_all_IOP_articles_dois_without_arxiv()
paths = get_arxivs_and_dois(dois)
print(paths)
