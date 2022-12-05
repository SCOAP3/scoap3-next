import os
from zipfile import ZipFile
import re
from invenio_search import current_search_client as es
from io import StringIO
import xml.etree.ElementTree as ET
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_files.api import Record
from invenio_db import db
import tarfile
import os
import csv
from datetime import datetime
import dateutil.parser as parser


def get_recids_and_record_creation_dates():
    query = {
        "_source": ["control_number", "record_creation_date", "dois"],
        "query": {
            "bool": {
                "must": [
                    {
                        "match": {
                            "imprints.publisher": "Elsevier"
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
    search_result = es.search(index="scoap3-records-record", scroll='1m', body=query)
    sid = search_result['_scroll_id']
    scroll_size = len(search_result['hits']['hits'])
    data = {}
    while (scroll_size > 0):
        for record_index in range(scroll_size):
            recid = search_result["hits"]["hits"][record_index]["_source"]["control_number"]
            creation_date = search_result["hits"]["hits"][record_index]["_source"]["record_creation_date"]
            doi = search_result["hits"]["hits"][record_index]["_source"]["dois"][0]["value"]
            data[doi] = {'recid': recid, 'creation_date': creation_date}
        search_result = es.scroll(scroll_id=sid, scroll='2m')
        sid = search_result['_scroll_id']
        scroll_size = len(search_result['hits']['hits'])
    return data


def parse_without_names_spaces(xml):
    it = ET.iterparse(StringIO(unicode(xml, "utf-8")))
    for _, el in it:
        _, _, el.tag = el.tag.rpartition("}")
    root = it.root
    return root


def get_record_creation_and_pdfa_dates(data_):
    path = '/data/harvesting/Elsevier/download/'
    pattern_doi = re.compile(r'.*<doi>(.*)<\/doi>.*')
    zips = [os.path.join(path, zip_file) for zip_file in os.listdir(path) if '.zip' in zip_file]
    all = []
    dois = data_.keys()
    for zip_file in zips:
        with ZipFile(zip_file, 'r') as zip:
            try:
                name = os.path.basename(zip_file).split('.')[0]
                data = ''.join(zip.read(name + '/dataset.xml').split())
                # doi_in_data = pattern_doi.search(data).group(1)
                # if doi_in_data in dois:
                element = parse_without_names_spaces(zip.read(name + '/dataset.xml'))
                one_article_data = element.findall('dataset-content/journal-item/[@cross-mark="true"]')
                for one_data in one_article_data:
                    doi = one_data.find('journal-item-unique-ids/doi').text
                    if doi in dois:
                        # creation_date = parser.parse(data_[doi]['creation_date']).replace(tzinfo=None)
                        # date = parser.parse(str(datetime.fromtimestamp(os.path.getmtime(zip_file))))
                        creation_date = parser.parse(data_[doi]['creation_date']).replace(tzinfo=None)
                        date = parser.parse(str(datetime.fromtimestamp(os.path.getmtime(zip_file)))).isoformat()
                        gap =(parser.parse(str(datetime.fromtimestamp(os.path.getmtime(zip_file)))) - parser.parse(data_[doi]['creation_date']).replace(tzinfo=None)).days
                        all.append([data_[doi]['recid'], doi, creation_date, date, gap])
                        # all[doi] = {'record_creation_date': creation_date, 'pdfa_receive_date': date, 'recid': data_[doi]['recid'], 'doi': doi}

            except:
                pass
    # average = sum(finals)/len(finals)
    header = ['control_number', 'doi', 'record_creation_date', 'pdfa_receive_date', 'interval between']
    with open('pdfas_and_records_receiving_comparison.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for one_record in all:
            writer.writerow(one_record)

    return all
