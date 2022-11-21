from invenio_search import current_search_client as es
from inspire_utils.record import get_value
from datetime import datetime
import dateutil.parser as parser
from invenio_pidstore.models import PersistentIdentifier
from invenio_records.api import Record
from invenio_db import db
from jsonschema.exceptions import ValidationError, SchemaError
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
                    "range": {"imprints.date": {"gte": "2020-01-31", "lte": "2022-12-31"}}
                }
            }
        }
    }
    search_results = es.search(index="scoap3-records-record", body=query)
    for search_result in search_results["hits"]["hits"]:
        try:
            doi = search_result["_source"]["dois"][0]["value"]
            dois.append(doi)
        except:
            pass
    return dois


def get_files_paths(dois, pattern_doi):
    path = "/data/harvesting/IOP/download/"
    xml_file_paths = []
    arxivs = {}
    zips = [os.path.join(path, zip_file) for zip_file in os.listdir(path) if '.zip' in zip_file]
    for zip_file in zips:
        with ZipFile(zip_file, 'r') as zip:
            # try:
                name = os.path.basename(zip_file).split('.')[0]
                all_files_names_in_zip = zip.namelist()
                for file_name in all_files_names_in_zip:
                    if 'xml' in file_name:
                        # data = zip.read(file_name)
                        # doi_in_data = pattern_doi.search(data).group(1)
                        # if doi_in_data in dois:
                        xml = zip.read(file_name)
                        arxivs[get_arxiv(xml).keys()[0]] = get_arxiv(xml)[get_arxiv(xml).keys()[0]]
                        xml_file_paths.append(file_name)

            # except:
            #     pass
    return arxivs


def parse_without_names_spaces(xml):
    it = ET.iterparse(StringIO((unicode(xml.encode('utf-8'), 'utf-8'))))
    for _, el in it:
        _, _, el.tag = el.tag.rpartition("}")
    root = it.root
    return root


def get_arxiv(xml):
    element = parse_without_names_spaces(xml)
    arxiv = element.find(
        "front/article-meta/custom-meta-group/custom-meta/meta-value"
    )
    doi = element.find("front/article-meta/article-id/[@pub-id-type='doi']")
    if arxiv is not None:
        return {doi.text: arxiv.text}
    return {doi.text: None}


pattern_doi = re.compile(r'.*<article-id pub-id-type="doi">(.*?)<\/article-id>.*')
dois = get_all_IOP_articles_dois_without_arxiv()
paths = get_files_paths(dois, pattern_doi)
print(paths)
