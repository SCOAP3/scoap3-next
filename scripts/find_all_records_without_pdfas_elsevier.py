from invenio_search import current_search_client as es
from io import StringIO
import xml.etree.ElementTree as ET
from zipfile import ZipFile
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_files.api import Record
from invenio_db import db
import os
import re


def get_all_elsevier_records_without_pdfa():
    no_pdfas = {}
    no_files_at_all = {}
    query = {
        "_source": ["_files", "control_number", "dois"],
        "query": {
            "bool": {
                "must": [
                    {
                        "match": {
                            "imprints.publisher": "Elsevier"
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
            try:
                files = search_result["hits"]["hits"][record_index]["_source"]["_files"]
            except:
                no_files_at_all[doi] = recid
            recid = search_result["hits"]["hits"][record_index]["_source"]["control_number"]
            doi = search_result["hits"]["hits"][record_index]["_source"]["dois"][0]["value"]
            types = []
            for file in files:
                types.append(file['filetype'])
            if 'pdf/a' not in types:
                no_pdfas[doi] = recid
        search_result = es.scroll(scroll_id=sid, scroll='2m')
        sid = search_result['_scroll_id']
        scroll_size = len(search_result['hits']['hits'])

    return no_pdfas


def parse_without_names_spaces(xml):
    it = ET.iterparse(StringIO(unicode(xml, "utf-8")))
    for _, el in it:
        _, _, el.tag = el.tag.rpartition("}")
    root = it.root
    return root


def find_articles_pdfa_with_xpath(dois_and_recids):
    path = '/data/harvesting/Elsevier/download/'
    pattern_doi = re.compile(r'.*<doi>(.*)<\/doi>.*')
    zips = [os.path.join(path, zip_file) for zip_file in os.listdir(path) if '.zip' in zip_file]
    finals = []
    dois = dois_and_recids.keys()
    for zip_file in zips:
        with ZipFile(zip_file, 'r') as zip:
            try:
                name = os.path.basename(zip_file).split('.')[0]
                data = ''.join(zip.read(name + '/dataset.xml').split())
                doi_in_data = pattern_doi.search(data).group(1)
                if doi_in_data in dois:
                    element = parse_without_names_spaces(zip.read(name + '/dataset.xml'))
                    one_article_data = element.findall('dataset-content/journal-item/[@cross-mark="true"]')
                    for one_data in one_article_data:
                        doi = one_data.find('journal-item-unique-ids/doi').text
                        if doi in dois:
                            pdf_path = one_data.find('files-info/web-pdf/pathname').text
                            pdfa_path = os.path.join(os.path.split(pdf_path)[0], 'main_a-2b.pdf')
                            finals.append({'doi': doi, 'pdfa': pdfa_path, 'dataset': name + '/dataset.xml', 'recid': dois_and_recids[doi], 'root_dir': name})
            except:
                pass
    return finals


dois_and_recids = get_all_elsevier_records_without_pdfa()
paths = find_articles_pdfa_with_xpath(dois_and_recids)


def update_records(data):
    path = '/data/harvesting/Elsevier/download'
    all_folders_in_download = os.listdir(path)
    dois = []
    for article_data in data:
        for folder in all_folders_in_download:
            if article_data['root_dir'] in folder:
                root_dir = folder
                break

        pid = PersistentIdentifier.get("recid", article_data['recid'])
        existing_record = Record.get_record(pid.object_uuid)
        zip_file_name = os.path.join(path, root_dir)
        with ZipFile(zip_file_name , 'r') as zip:
            file_ = {
                "url": os.path.join(article_data['root_dir'], article_data['pdfa']),
                "name": "{0}_a.{1}".format(article_data['doi'], "pdf"),
                "filetype": "pdf/a",
            }
            f = zip.open(file_["url"])
            existing_record.files[file_["name"]] = f
            existing_record.files[file_["name"]]["filetype"] = file_["filetype"]
            existing_record.commit()
            db.session.commit()
            dois.append(article_data['doi'])
            print(article_data['root_dir'])
    print('Updated:', dois)

    update_records(paths)
