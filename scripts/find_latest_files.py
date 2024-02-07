import os
from datetime import datetime
from invenio_search import current_search_client as es
from io import StringIO
import xml.etree.ElementTree as ET
from zipfile import ZipFile
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_files.api import Record
from invenio_db import db
import os
import re
#4 scoap3-worker-69f8c4c579-6lrv9
def find_latest_files_locations():
    files_for_update = {}
    f = open("./final_missing_paths.txt")
    for line in f:
        parts = line.split()
        doi = parts[0]
        xml = parts[1]
        pdf = parts[2]
        date = parts[3]
        type_= parts[6]
        if doi in files_for_update:
            if type_ in files_for_update[doi]:
                if datetime.strptime(files_for_update[doi][type_]["date"], "%Y-%M-%d") < datetime.strptime(date, "%Y-%M-%d"):
                    if type_ == "xml" and "main.xml" in xml:
                        files_for_update[doi][type_] = {"file": xml, "date": date}
                    elif type_ == "pdf" and "main.pdf" in pdf:
                        files_for_update[doi][type_] = {"file": pdf, "date": date}
                elif type_ == "pdf/a" and "main.pdf" in pdf and datetime.strptime(files_for_update[doi][type_]["date"], "%Y-%M-%d") < datetime.strptime(date, "%Y-%M-%d"):
                    if "vtex" in pdf:
                        pdfa_path = os.path.join(os.path.split(pdf)[0], 'main_a-2b.pdf')
                        files_for_update[doi][type_] = {"file": pdfa_path, "date": date}
            else:
                if type_ == "xml" and "main.xml" in xml:
                    files_for_update[doi][type_] = {"file": xml, "date": date}
                elif type_ == "pdf" and "main.pdf" in pdf:
                    files_for_update[doi][type_] = {"file": pdf, "date": date}
                elif type_ == "pdf/a" and "main.pdf" in pdf:
                    if "vtex" in pdf:
                        pdfa_path = os.path.join(os.path.split(pdf)[0], 'main_a-2b.pdf')
                        files_for_update[doi][type_] = {"file": pdfa_path, "date": date}

        else:
            files_for_update[doi]={}
            if type_ == "xml" and "main.xml" in xml:
                files_for_update[doi][type_] = {"file": xml, "date": date}
            elif type_ == "pdf" and "main.pdf" in pdf:
                files_for_update[doi][type_] = {"file": pdf, "date": date}
            elif type_ == "pdf/a" and "main.pdf" in pdf:
                if "vtex" in pdf:
                    pdfa_path = os.path.join(os.path.split(pdf)[0], 'main_a-2b.pdf')
                    files_for_update[doi][type_] = {"file": pdfa_path, "date": date}
    f.close()
    return files_for_update



def update_records(data):
    for doi in data:
        query = {
            "query": {
                "bool": {
                    "must": [{"match": {"dois.value": doi}}],
                }
            }
        }
        search_result = es.search(index="scoap3-records-record", body=query)
        recid = search_result["hits"]["hits"][0]["_source"]["control_number"]
        pid = PersistentIdentifier.get("recid", recid)
        existing_record = Record.get_record(pid.object_uuid)
        for type_ in data[doi]:
            if type_ == "pdf/a":
                file_name = doi +"_a" + "." + "pdf"
            else:
                file_name = doi + "." + type_
            f = open(data[doi][type_]["file"])
            print('PROCESSING:', "doi=", doi, " type=", type_, "file_name=", file_name)
            existing_record.files[file_name] = f
            existing_record.files[file_name]["filetype"] = type_
            existing_record.commit()
            db.session.commit()
            print('Updated:', "doi=", doi, " type=", type_, file_name)
            #break
        # break

