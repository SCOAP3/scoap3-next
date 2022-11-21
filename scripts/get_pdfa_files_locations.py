import os
from zipfile import ZipFile
import re
from invenio_search import current_search_client as es
from io import StringIO
import xml.etree.ElementTree as ET
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_files.api import Record
from invenio_db import db


def find_articles_dois():
    dois_and_recids = {}
    recids = [66172, 66187, 66234, 66412, 67067, 67089, 67120, 67154, 67155, 67156, 67157, 67159, 67160, 67187, 67188, 67208, 67209, 67218, 67254, 67258, 67279, 67280, 67281, 67298, 67299, 67300, 67301, 67302, 67319, 67320, 67705, 67706, 67776, 67778, 67780, 67782, 68819, 68832, 68833, 68834, 68836, 68838, 68852, 68854, 68855, 68856, 68857, 68858, 68859, 68860, 68880, 68881, 68882, 68883, 68884, 68885, 68886, 68887, 68888, 68889, 68891, 68892, 68893, 68895, 68896, 68904, 68905, 68906, 68907, 68908, 68912, 68913, 68914, 68915, 68999, 69001, 69002, 69003, 69004, 69005, 69015, 69020, 69024, 69026, 69027, 69028, 69029, 69030, 69031, 69041, 69084, 69132, 69135, 69153, 69154, 69159, 69166, 69167, 69168, 69169, 69171, 69178, 69188, 69189, 69201, 69220, 69222, 69223, 69224, 69225, 69333, 69334, 69335, 69336, 69337, 69338, 69339, 69355, 69403, 69404, 69420, 69445, 69446, 69505, 69524, 69525, 69526, 69541, 69542, 69551, 69572, 69573]

    for recid in recids:
        query = {
            "query": {
                "bool": {
                    "must": [{"match": {"control_number": str(recid)}}],
                }
            }
        }
        search_result = es.search(index="scoap3-records-record", body=query)
        try:
            doi = search_result["hits"]["hits"][0]["_source"]["dois"][0]["value"]
            dois_and_recids[doi] = recid
        except:
            pass
    return dois_and_recids


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


def update_records(data):
    path = '/data/harvesting/Elsevier/unpacked'
    all_folders_in_upacked = os.listdir(path)
    dois = []
    for article_data in data:
        for folder in all_folders_in_upacked:
            if article_data['root_dir'] in folder:
                root_dir = folder
                break

        pid = PersistentIdentifier.get("recid", article_data['recid'])
        existing_record = Record.get_record(pid.object_uuid)
        file_ = {
            "url": os.path.join(path, root_dir, article_data['root_dir'], article_data['pdfa']),
            "name": "{0}_a.{1}".format(article_data['doi'], "pdf"),
                    "filetype": "pdf/a",
        }
        f = open(file_["url"])
        existing_record.files[file_["name"]] = f
        existing_record.files[file_["name"]]["filetype"] = file_["filetype"]
        existing_record.commit()
        db.session.commit()
        dois.append(article_data['doi'])
    print('Updated:', dois)
update_records(find_articles_pdfa_with_xpath(find_articles_dois()))

