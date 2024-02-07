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
    dois = ["10.1016/j.physletb.2021.136192",
"10.1016/j.physletb.2021.136193",
"10.1016/j.physletb.2021.136190",
"10.1016/j.physletb.2021.136191",
"10.1016/j.physletb.2021.136196",
"10.1016/j.physletb.2021.136197",
"10.1016/j.physletb.2021.136194",
"10.1016/j.physletb.2021.136195",
"10.1016/j.physletb.2021.136198",
"10.1016/j.physletb.2021.136199",
"10.1016/j.physletb.2021.136162",
"10.1016/j.physletb.2021.136161",
"10.1016/j.physletb.2021.136160",
"10.1016/j.physletb.2021.136228",
"10.1016/j.physletb.2021.136229",
"10.1016/j.physletb.2021.136224",
"10.1016/j.physletb.2021.136225",
"10.1016/j.physletb.2021.136226",
"10.1016/j.physletb.2021.136227",
"10.1016/j.physletb.2021.136220",
"10.1016/j.physletb.2021.136221",
"10.1016/j.physletb.2021.136222",
"10.1016/j.physletb.2021.136223",
"10.1016/j.nuclphysb.2021.115360",
"10.1016/j.nuclphysb.2021.115361",
"10.1016/j.nuclphysb.2021.115362",
"10.1016/j.nuclphysb.2021.115363",
"10.1016/j.nuclphysb.2021.115364",
"10.1016/j.nuclphysb.2021.115365",
"10.1016/j.nuclphysb.2021.115366",
"10.1016/j.nuclphysb.2021.115367",
"10.1016/j.nuclphysb.2021.115368",
"10.1016/j.nuclphysb.2021.115370",
"10.1016/j.physletb.2021.136156",
"10.1016/j.physletb.2021.136157",
"10.1016/j.physletb.2021.136154",
"10.1016/j.physletb.2021.136155",
"10.1016/j.physletb.2021.136152",
"10.1016/j.physletb.2021.136153",
"10.1016/j.physletb.2021.136150",
"10.1016/j.physletb.2021.136151",
"10.1016/j.physletb.2021.136158",
"10.1016/j.physletb.2021.136159",
"10.1016/j.physletb.2021.136123",
"10.1016/j.physletb.2021.136122",
"10.1016/j.physletb.2021.136127",
"10.1016/j.physletb.2021.136125",
"10.1016/j.physletb.2021.136124",
"10.1016/j.physletb.2021.136129",
"10.1016/j.physletb.2021.136128",
"10.1016/j.physletb.2021.136277",
"10.1016/j.physletb.2021.136276",
"10.1016/j.physletb.2021.136275",
"10.1016/j.physletb.2021.136274",
"10.1016/j.physletb.2021.136273",
"10.1016/j.physletb.2021.136271",
"10.1016/j.physletb.2021.136270",
"10.1016/j.physletb.2021.136181",
"10.1016/j.physletb.2021.136180",
"10.1016/j.physletb.2021.136183",
"10.1016/j.physletb.2021.136182",
"10.1016/j.physletb.2021.136185",
"10.1016/j.physletb.2021.136184",
"10.1016/j.physletb.2021.136187",
"10.1016/j.physletb.2021.136186",
"10.1016/j.physletb.2021.136189",
"10.1016/j.physletb.2021.136188",
"10.1016/j.physletb.2021.136118",
"10.1016/j.physletb.2021.136119",
"10.1016/j.physletb.2021.136113",
"10.1016/j.physletb.2021.136239",
"10.1016/j.physletb.2021.136238",
"10.1016/j.physletb.2021.136278",
"10.1016/j.nuclphysb.2021.115359",
"10.1016/j.nuclphysb.2021.115358",
"10.1016/j.nuclphysb.2021.115355",
"10.1016/j.nuclphysb.2021.115354",
"10.1016/j.nuclphysb.2021.115357",
"10.1016/j.nuclphysb.2021.115356",
"10.1016/j.nuclphysb.2021.115353",
"10.1016/j.nuclphysb.2021.115352",
"10.1016/j.physletb.2021.136249",
"10.1016/j.physletb.2021.136246",
"10.1016/j.physletb.2021.136247",
"10.1016/j.physletb.2021.136244",
"10.1016/j.physletb.2021.136245",
"10.1016/j.physletb.2021.136242",
"10.1016/j.physletb.2021.136243",
"10.1016/j.physletb.2021.136240",
"10.1016/j.physletb.2021.136241",
"10.1016/j.physletb.2021.136145",
"10.1016/j.physletb.2021.136144",
"10.1016/j.physletb.2021.136147",
"10.1016/j.physletb.2021.136146",
"10.1016/j.physletb.2021.136141",
"10.1016/j.physletb.2021.136140",
"10.1016/j.physletb.2021.136143",
"10.1016/j.physletb.2021.136142",
"10.1016/j.physletb.2021.136149",
"10.1016/j.physletb.2021.136148",
"10.1016/j.nuclphysb.2021.115391",
"10.1016/j.nuclphysb.2021.115393",
"10.1016/j.nuclphysb.2021.115394",
"10.1016/j.physletb.2021.136202",
"10.1016/j.physletb.2021.136203",
"10.1016/j.physletb.2021.136200",
"10.1016/j.physletb.2021.136201",
"10.1016/j.physletb.2021.136206",
"10.1016/j.physletb.2021.136207",
"10.1016/j.physletb.2021.136204",
"10.1016/j.physletb.2021.136205",
"10.1016/j.physletb.2021.136208",
"10.1016/j.physletb.2021.136209",
"10.1016/j.nuclphysb.2021.115369",
"10.1016/j.physletb.2021.136101",
"10.1016/j.nuclphysb.2021.115342",
"10.1016/j.nuclphysb.2021.115343",
"10.1016/j.nuclphysb.2021.115340",
"10.1016/j.nuclphysb.2021.115341",
"10.1016/j.physletb.2021.136259",
"10.1016/j.physletb.2021.136258",
"10.1016/j.physletb.2021.136255",
"10.1016/j.physletb.2021.136254",
"10.1016/j.physletb.2021.136257",
"10.1016/j.physletb.2021.136256",
"10.1016/j.physletb.2021.136251",
"10.1016/j.physletb.2021.136250",
"10.1016/j.physletb.2021.136253",
"10.1016/j.physletb.2021.136252",
"10.1016/j.nuclphysb.2021.115339",
"10.1016/j.nuclphysb.2021.115338",
"10.1016/j.nuclphysb.2021.115337",
"10.1016/j.nuclphysb.2021.115336",
"10.1016/j.nuclphysb.2021.115335",
"10.1016/j.nuclphysb.2021.115334",
"10.1016/j.nuclphysb.2021.115333",
"10.1016/j.nuclphysb.2021.115332",
"10.1016/j.physletb.2021.136211",
"10.1016/j.physletb.2021.136210",
"10.1016/j.physletb.2021.136218",
"10.1016/j.physletb.2021.136171",
"10.1016/j.physletb.2021.136172",
"10.1016/j.physletb.2021.136173",
"10.1016/j.physletb.2021.136174",
"10.1016/j.physletb.2021.136175",
"10.1016/j.physletb.2021.136176",
"10.1016/j.physletb.2021.136177",
"10.1016/j.physletb.2021.136178",
"10.1016/j.physletb.2021.136179",
"10.1016/j.nuclphysb.2021.115388",
"10.1016/j.nuclphysb.2021.115389",
"10.1016/j.nuclphysb.2021.115387",
"10.1016/j.nuclphysb.2021.115384",
"10.1016/j.nuclphysb.2021.115385",
"10.1016/j.nuclphysb.2021.115371",
"10.1016/j.physletb.2021.136213",
"10.1016/j.physletb.2021.136212",
"10.1016/j.physletb.2021.136215",
"10.1016/j.physletb.2021.136214",
"10.1016/j.physletb.2021.136217",
"10.1016/j.physletb.2021.136216",
"10.1016/j.physletb.2021.136219",
"10.1016/j.nuclphysb.2021.115373",
"10.1016/j.nuclphysb.2021.115372",
"10.1016/j.nuclphysb.2021.115377",
"10.1016/j.nuclphysb.2021.115375",
"10.1016/j.nuclphysb.2021.115374",
"10.1016/j.physletb.2021.136282",
"10.1016/j.physletb.2021.136134",
"10.1016/j.physletb.2021.136135",
"10.1016/j.physletb.2021.136136",
"10.1016/j.physletb.2021.136137",
"10.1016/j.physletb.2021.136130",
"10.1016/j.physletb.2021.136131",
"10.1016/j.physletb.2021.136132",
"10.1016/j.physletb.2021.136133",
"10.1016/j.physletb.2021.136138",
"10.1016/j.physletb.2021.136139",
"10.1016/j.physletb.2021.136268",
"10.1016/j.physletb.2021.136269",
"10.1016/j.physletb.2021.136260",
"10.1016/j.physletb.2021.136261",
"10.1016/j.physletb.2021.136262",
"10.1016/j.physletb.2021.136263",
"10.1016/j.physletb.2021.136264",
"10.1016/j.physletb.2021.136265",
"10.1016/j.physletb.2021.136266",
"10.1016/j.physletb.2021.136267"]
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
            recid = search_result["hits"]["hits"][0]["_source"]["control_number"]
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
    path = '/data/harvesting/Elsevier/download'
    all_folders_in_download = os.listdir(path)
    dois = []
    for article_data in data:
        for folder in all_folders_in_download:
            if article_data['root_dir'] in folder:
                root_dir = folder
                break
        path_to_zip = path + "/" + article_data['root_dir'] + ".zip"
        with ZipFile(path_to_zip, 'r') as zip:
            pid = PersistentIdentifier.get("recid", article_data['recid'])
            existing_record = Record.get_record(pid.object_uuid)
            file_ = {
                "url": os.path.join(path, root_dir, article_data['root_dir'], article_data['pdfa']),
                "name": "{0}_a.{1}".format(article_data['doi'], "pdf"),
                        "filetype": "pdf/a",
            }
            import tempfile
            with tempfile.TemporaryFile(mode='wb+') as temp_file:  # 'wb+' mode for
                temp_file.write(zip.read(os.path.join(article_data['root_dir'], article_data['pdfa'])))
                temp_file.flush()  # Ensure all data is written
                temp_file.seek(0)  # Move the file pointer to the beginning of the file
            # f = zip.read(os.path.join(article_data['root_dir'], article_data['pdfa']))
                print(file_)
                # existing_record.files[file_["name"]] = temp_file
                # existing_record.files[file_["name"]]["filetype"] = file_["filetype"]
                # existing_record.commit()
                # db.session.commit()
                dois.append(article_data['doi'])
    print('Updated:', dois)
    return dois
update_records(find_articles_pdfa_with_xpath(find_articles_dois()))

