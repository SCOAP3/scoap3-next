from invenio_search import current_search_client as es
import xml.etree.ElementTree as ET
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_files.api import Record
from invenio_db import db
import os
import re

common = [u'10.1088/1674-1137/ac2a25',
 u'10.1088/1674-1137/ac2b12',
 u'10.1088/1674-1137/ac6cd3',
 u'10.1088/1674-1137/ac6cd5',
 u'10.1088/1674-1137/ac66cc',
 u'10.1088/1674-1137/ac67d0',
 u'10.1088/1674-1137/ac6d4e',
 u'10.1088/1674-1137/ac68da',
 u'10.1088/1674-1137/ac6665',
 u'10.1088/1674-1137/abe19b',
 u'10.1088/1674-1137/abde2e',
 u'10.1088/1674-1137/abe195',
 u'10.1088/1674-1137/abdf43',
 u'10.1088/1674-1137/abe199',
 u'10.1088/1674-1137/ac5b0e',
 u'10.1088/1674-1137/abc244',
 u'10.1088/1674-1137/abc538',
 u'10.1088/1674-1137/abc539',
 u'10.1088/1674-1137/abc682',
 u'10.1088/1674-1137/abc683',
 u'10.1088/1674-1137/abc0cc',
 u'10.1088/1674-1137/abc169',
 u'10.1088/1674-1137/abc245',
 u'10.1088/1674-1137/abf13a',
 u'10.1088/1674-1137/ac0c6f',
 u'10.1088/1674-1137/ac0ee2',
 u'10.1088/1674-1137/acaf26',
 u'10.1088/1674-1137/acc1cf',
 u'10.1088/1674-1137/ac9896',
 u'10.1088/1674-1137/abcd90',
 u'10.1088/1674-1137/ac0ee4',
 u'10.1088/1674-1137/ac0e88',
 u'10.1088/1674-1137/ac0e8a',
 u'10.1088/1674-1137/ac1575',
 u'10.1088/1674-1137/abccac',
 u'10.1088/1674-1137/abd16d',
 u'10.1088/1674-1137/ac68d7',
 u'10.1088/1674-1137/ac4df1',
 u'10.1088/1674-1137/ac6490',
 u'10.1088/1674-1137/ac5fa2',
 u'10.1088/1674-1137/abdfbe',
 u'10.1088/1674-1137/abe110',
 u'10.1088/1674-1137/abe197',
 u'10.1088/1674-1137/abe19a',
 u'10.1088/1674-1137/acac6d',
 u'10.1088/1674-1137/acac69',
 u'10.1088/1674-1137/acbbc0',
 u'10.1088/1674-1137/abcc5b',
 u'10.1088/1674-1137/acc641',
 u'10.1088/1674-1137/ac1668',
 u'10.1088/1674-1137/abfe51',
 u'10.1088/1674-1137/abfc38',
 u'10.1088/1674-1137/abf828',
 u'10.1088/1674-1137/abfb50',
 u'10.1088/1674-1137/abfb5f',
 u'10.1088/1674-1137/ac9de9',
 u'10.1088/1674-1137/aca38d',
 u'10.1088/1674-1137/ac9deb',
 u'10.1088/1674-1137/ac957b',
 u'10.1088/1674-1137/ac9895',
 u'10.1088/1674-1137/aca00d',
 u'10.1088/1674-1137/ac9897',
 u'10.1088/1674-1137/aca585',
 u'10.1088/1674-1137/aca8f6',
 u'10.1088/1674-1137/ac92d8',
 u'10.1088/1674-1137/abd084',
 u'10.1088/1674-1137/abce50',
 u'10.1088/1674-1137/abd01a',
 u'10.1088/1674-1137/abcfac',
 u'10.1088/1674-1137/abe03c',
 u'10.1088/1674-1137/aca1aa',
 u'10.1088/1674-1137/ac3fab',
 u'10.1088/1674-1137/ac21b8',
 u'10.1088/1674-1137/ac1d9c',
 u'10.1088/1674-1137/ac224b',
 u'10.1088/1674-1137/ac1e09',
 u'10.1088/1674-1137/ac0e8b',
 u'10.1088/1674-1137/ac1bfd',
 u'10.1088/1674-1137/ac1b9a',
 u'10.1088/1674-1137/ac1ef9',
 u'10.1088/1674-1137/ac4704',
 u'10.1088/1674-1137/ac4ee8',
 u'10.1088/1674-1137/ac1c66',
 u'10.1088/1674-1137/ac4f4c',
 u'10.1088/1674-1137/ac87f1',
 u'10.1088/1674-1137/abcfaa',
 u'10.1088/1674-1137/ac878c',
 u'10.1088/1674-1137/ac8bc9',
 u'10.1088/1674-1137/acc3f4',
 u'10.1088/1674-1137/ac90af',
 u'10.1088/1674-1137/acc4ab',
 u'10.1088/1674-1137/abcfab',
 u'10.1088/1674-1137/abe9a2',
 u'10.1088/1674-1137/abf9ff',
 u'10.1088/1674-1137/abe8cf',
 u'10.1088/1674-1137/abfd28',
 u'10.1088/1674-1137/ac2f95',
 u'10.1088/1674-1137/ac2ed1',
 u'10.1088/1674-1137/ac6573',
 u'10.1088/1674-1137/ac6cd8',
 u'10.1088/1674-1137/ac6cd6',
 u'10.1088/1674-1137/ac6d51',
 u'10.1088/1674-1137/ac5c2e',
 u'10.1088/1674-1137/ac6b92',
 u'10.1088/1674-1137/aca959',
 u'10.1088/1674-1137/ac9d28',
 u'10.1088/1674-1137/abce4f',
 u'10.1088/1674-1137/abd088',
 u'10.1088/1674-1137/abce10',
 u'10.1088/1674-1137/abcf22',
 u'10.1088/1674-1137/abd92a',
 u'10.1088/1674-1137/ac8651',
 u'10.1088/1674-1137/abc1d5',
 u'10.1088/1674-1137/abc242',
 u'10.1088/1674-1137/abc241',
 u'10.1088/1674-1137/acc92d',
 u'10.1088/1674-1137/abeb07',
 u'10.1088/1674-1137/abf4f6',
 u'10.1088/1674-1137/abe36d',
 u'10.1088/1674-1137/abefca',
 u'10.1088/1674-1137/ac3fac',
 u'10.1088/1674-1137/ac3fae',
 u'10.1088/1674-1137/ac3d2b',
 u'10.1088/1674-1137/ac3faa',
 u'10.1088/1674-1137/ac061c',
 u'10.1088/1674-1137/ac88bb',
 u'10.1088/1674-1137/acaa22',
 u'10.1088/1674-1137/ac930b',
 u'10.1088/1674-1137/ac92da',
 u'10.1088/1674-1137/ac89d1',
 u'10.1088/1674-1137/ac8cd5',
 u'10.1088/1674-1137/ac8789',
 u'10.1088/1674-1137/ac89d0',
 u'10.1088/1674-1137/aca888',
 u'10.1088/1674-1137/ac80b4',
 u'10.1088/1674-1137/ac957c']

def gel_records_from_2020_artids():
    records_ = {}
    query = {
        "_source": ["publication_info", "control_number", "dois"],
        "query": {
            "bool": {
                "must": [
                    {
                        "match": {
                            "imprints.publisher": "IOP"
                        }
                    },
                     {
                        "range": {
                            "imprints.date": {
                                "gte": "2020-01-01"
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
    while (scroll_size > 0):
        for record_index in range(scroll_size):
            recid = search_result["hits"]["hits"][record_index]["_source"]["control_number"]
            artid = search_result["hits"]["hits"][record_index]["_source"]["publication_info"][0]["artid"]
            doi = search_result["hits"]["hits"][record_index]["_source"]["dois"][0]["value"]
            if doi in common:
                records_[artid] = recid
        search_result = es.scroll(scroll_id=sid, scroll='2m')
        sid = search_result['_scroll_id']
        scroll_size = len(search_result['hits']['hits'])

    return records_



def parse_to_ET_element(article):
    parser = ET.XMLParser(encoding="utf-8")
    return ET.fromstring(article, parser=parser)

def get_all_iop_xml_files(records):
    path = '/data/harvesting/IOP/unpacked/'
    recids_and_paths = {}
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            if not ".xml" in name:
                continue
            artid_from_file_name = name.split("_")[-1].split(".")[0]
            if artid_from_file_name in records.keys():
                recids_and_paths[records[artid_from_file_name]] = os.path.join(root, name)
    return recids_and_paths

def extract_text(article, path, field_name):
    try:
        return  article.find(path).text
    except AttributeError:
        print(field_name + " is not found in XML, " )
        return

class IOPParser():
    def __init__(self, article):
        self.article = article
        self.dois = None

    def result(self):
        return  self._extract_authors()

    def _get_dois(self):
        node = self.article.find("front/article-meta/article-id/[@pub-id-type='doi']")
        if node is None:
            return
        dois = node.text
        if dois:
            self.dois = dois
            return [dois]
        return

    def _extract_authors(self):
        contrib_types = self.article.findall(
            "front/article-meta/contrib-group/contrib[@contrib-type='author']"
        )
        authors = []
        surname = ""
        given_names = ""

        for contrib_type in contrib_types:
            surname = self._extract_surname(contrib_type)
            given_names = self._extract_given_names(contrib_type)
            reffered_ids = contrib_type.findall("xref[@ref-type='aff']")
            affiliations = [
                self._get_affiliation_value(self.article, reffered_id)
                for reffered_id in reffered_ids
                if self._get_affiliation_value(self.article, reffered_id)
            ]
            email = self._extract_email(contrib_type)
            author = {}
            if surname:
                author["surname"] = surname
            if given_names:
                author["given_names"] = given_names
            if email:
                author["email"] = email
            if affiliations:
                author["affiliations"] = affiliations
            if author:
                authors.append(author)
        return authors

    def _extract_email(self, contrib_type):
        return extract_text(
            article=contrib_type,
            path="email",
            field_name="email",
        )

    def _extract_surname(self, contrib_type):
        return extract_text(
            article=contrib_type,
            path="name/surname",
            field_name="surname",
        )

    def _extract_given_names(self, contrib_type):
        REMOVE_SPECIAL_CHARS = re.compile(r"[^A-Za-z0-9\s\,\.]+")
        try:
            given_names = contrib_type.find("name/given-names").text
            if "collaboration" not in given_names.lower():
                return given_names
            else:
                self.collaborations.append(REMOVE_SPECIAL_CHARS.sub("", given_names))
        except AttributeError:
            print("Given_names is not found in XML", self.dois)

    def _get_affiliation_value(self, article, reffered_id):
        institution_and_country = {}
        rid = reffered_id.get("rid")
        institution = self._get_institution(article, rid)
        country = self._get_country(article, rid)
        if country is not None:
            institution_and_country["country"] = country.text.decode("ascii")
        if institution is not None and country is not None:
            institution_and_country["institution"] = ", ".join(
                [institution.text.decode("ascii"), country.text.decode("ascii")]
            )
        else:
            return self._get_affiliation(article, rid)

        return institution_and_country

    def _get_institution(self, article, id):
        return article.find('front/article-meta/contrib-group/aff[@id="'+id+'"]/institution')

    def _get_country(self, article, id):
        return article.find("./front/article-meta/contrib-group/aff[@id='" + id +"']/country")

    def _get_orcid(self, article, id):
        return article.find("./front/article-meta/contrib-group/aff[@id='" + id +"']/country")

    def _get_affiliation(self, article, id):
        value = ET.tostring(article.find("./front/article-meta/contrib-group/aff[@id='" + id +"']"))
        without_spaces = ' '.join(value.split())
        value =  re.search('</label>(.*)</aff>', without_spaces).group(1).strip()
        return {'country': value.split(',')[-1].strip(), 'value': value}


def parse_authors(recids_and_paths):
    parsed_authors_list = {}
    for recid in recids_and_paths:
        path = recids_and_paths[recid]
        with open(path) as f:
            element = parse_to_ET_element(f.read())
            parser = IOPParser(element)
            result = parser.result()
            parsed_authors_list[recid] = result
    return parsed_authors_list

dois = []
def update_records(data):
    recids = data.keys()
    for recid in recids:
        pid = PersistentIdentifier.get("recid", recid)
        existing_record = Record.get_record(pid.object_uuid)
        existing_record['authors'] = data[recid]
        existing_record.commit()
        db.session.commit()
        dois.append(existing_record['dois'][0]['value'])
        print('Updated:', recid, " DOI:", existing_record['dois'][0]['value'])

records = gel_records_from_2020_artids()
results = get_all_iop_xml_files(records)
data = parse_authors({"61271": results["61271"]})
update_records(data)