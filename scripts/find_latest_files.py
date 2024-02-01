import os
from zipfile import ZipFile
from datetime import datetime
import re
from invenio_search import current_search_client as es
from io import StringIO
import xml.etree.ElementTree as ET
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_files.api import Record
from invenio_db import db
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
                    if type_ == "xml":
                        files_for_update[doi][type_] = {"file": xml, "date": date}
                    elif type_ == "pdf":
                        files_for_update[doi][type_] = {"file": pdf, "date": date}
                    elif type_ == "pdf/a":
                        pdfa_path = os.path.join(os.path.split(pdf)[0], 'main_a-2b.pdf')
                        files_for_update[doi][type_] = {"file": pdfa_path, "date": date}
            else:
                if type_ == "xml":
                    files_for_update[doi][type_] = {"file": xml, "date": date}
                elif type_ == "pdf":
                    files_for_update[doi][type_] = {"file": pdf, "date": date}
                elif type_ == "pdf/a":
                    pdfa_path = os.path.join(os.path.split(pdf)[0], 'main_a-2b.pdf')
                    files_for_update[doi][type_] = {"file": pdfa_path, "date": date}

        else:
            files_for_update[doi]={}
            if type_ == "xml":
                files_for_update[doi][type_] = {"file": xml, "date": date}
            elif type_ == "pdf":
                files_for_update[doi][type_] = {"file": pdf, "date": date}
            elif type_ == "pdf/a":
                pdfa_path = os.path.join(os.path.split(pdf)[0], 'main_a-2b.pdf')
                files_for_update[doi][type_] = {"file": pdfa_path, "date": date}
    f.close()
    return files_for_update


