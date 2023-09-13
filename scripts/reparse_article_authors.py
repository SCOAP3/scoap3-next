from invenio_search import current_search_client as es
import xml.etree.ElementTree as ET
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_files.api import Record
from invenio_db import db
import os
import re

def gel_records_from_2020_artids():
    records_ = {}
    query = {
        "_source": ["publication_info", "control_number"],
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
        if country:
            institution_and_country["country"] = country.text
        if institution and country:
            institution_and_country["institution"] = ", ".join(
                [institution.text, country.text]
            )
        else:
            return self._get_affiliation(article, rid)

        return institution_and_country

    def _get_institution(self, article, id):
        return article.find('front/article-meta/contrib-group/aff[@id="'+id+'"]/institution')

    def _get_country(self, article, id):
        return article.find("./front/article-meta/contrib-group/aff[@id='" + id +"']/country")

    def _get_affiliation(self, article, id):
        value = ET.tostring(article.find("./front/article-meta/contrib-group/aff[@id='" + id +"']"))
        without_spaces = ' '.join(value.split())
        value =  re.search('</label>(.*)</aff>', without_spaces).group(1).strip()
        return {'country': value.split(',')[-1], 'value': value}


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


def update_records(data):
    recids = data.keys()
    for recid in recids:
        pid = PersistentIdentifier.get("recid", recid)
        existing_record = Record.get_record(pid.object_uuid)
        existing_record['authors'] = data[recid]
        existing_record.commit()
        db.session.commit()
    print('Updated:', recid)

records = gel_records_from_2020_artids()
results = get_all_iop_xml_files(records)
data = parse_authors({"61453":results['61453']})
update_records(data)