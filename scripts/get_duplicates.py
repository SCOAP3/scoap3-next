from invenio_search import current_search_client as es
from inspire_utils.record import get_value
from datetime import datetime
import dateutil.parser as parser
from invenio_pidstore.models import PersistentIdentifier
from invenio_records.api import Record
from invenio_db import db
from jsonschema.exceptions import ValidationError, SchemaError
from invenio_records_files.api import Record


def find_duplicates_dois():
    query = {
        "size": 1,
        "query": {
            "match_all": {}}
    }

    page = es.search(index="scoap3-records-record", scroll='1m', body=query)
    sid = page['_scroll_id']
    scroll_size = len(page['hits']['hits'])
    records = {}
    while (scroll_size > 0):
        for record_index in range(scroll_size):
            recid = get_value(page["hits"]["hits"][record_index], "_source.control_number" , "")
            doi = page["hits"]["hits"][record_index]["_source"]["dois"][0]['value']
            files = attach_files(page["hits"]["hits"][record_index])
            update_date = page["hits"]["hits"][record_index]["_source"]["_updated"]
            if doi not in records:
                records[doi] = {'count': 1, 'data': {}}
                records[doi]['data'][recid] = {'files': files, 'update_date': update_date}
            else:
                records[doi]['count'] = records[doi]['count'] + 1
                records[doi]['data'][recid] = {'files': files, 'update_date': update_date}
        page = es.scroll(scroll_id=sid, scroll='2m')
        sid = page['_scroll_id']
        scroll_size = len(page['hits']['hits'])
    final_records = {k: v for k, v in records.items() if v['count'] >= 2}

    return final_records


def attach_files(record):
    files = {}
    for file in get_value(record, "_source._files", []):
        files[get_value(file, 'filetype', "")] = file
    return files


def get_updated_date(record):
    return parser.parse(record['update_date']).isoformat()


def find_the_newest_record(duplicated_records):
    date = None
    newest_record_rec_id = None
    for recid in duplicated_records.keys():
        update_date = get_updated_date(duplicated_records[recid])
        if not date and not newest_record_rec_id:
            date = update_date
            newest_record_rec_id = recid
        elif date < update_date :
            newest_record_rec_id = recid
            date = update_date
    return newest_record_rec_id


def find_all_missing_files(duplicated_records, newest_record_files):
    file_types = newest_record_files.keys()
    missing_files=[]
    for recid in duplicated_records.keys():
        files = duplicated_records[recid]['files']
        for file_type_form_the_record in files.keys():
            if file_type_form_the_record not in file_types:
                missing_files.append(files[file_type_form_the_record])
    if len(missing_files) == 0:
        print('Nothing to update')
        return []
    return missing_files

def updated_files(duplicated_records, newest_record_files):
    files_from_newest_record = [newest_record_files[file_type] for file_type in newest_record_files.keys()]
    missing_files = find_all_missing_files(duplicated_records, newest_record_files)
    if missing_files:
        return  files_from_newest_record + missing_files
    return []


def delete_duplicates(records):
    dois= records.keys()
    updated = []
    for doi in dois:
        print('Duplicate of ', doi, 'will be deleted')
        newest_record_id = find_the_newest_record(records[doi]['data'])
        print('keep the article with recid: ', newest_record_id)
        newest_record_files = records[doi]['data'][newest_record_id]['files']
        all_files = updated_files(records[doi]['data'], newest_record_files)
        all_rec_ids = records[doi]['data'].keys()
        all_rec_ids.remove(newest_record_id)
        if all_files:
            update_the_record(newest_record_id, all_files)
            for recid_to_delete in all_rec_ids:
                delete_record(recid_to_delete)
        else:
            for recid_to_delete in all_rec_ids:
                delete_record(recid_to_delete)


def update_the_record(recid, files):
    pid = PersistentIdentifier.get("recid", recid)
    record = Record.get_record(pid.object_uuid)
    record['_files'] = files
    print("Updated records ", recid)
    try:
        record.commit()
        db.session.commit()
    except ValidationError as err:
        print("Validation error: %s." % err,)
    except SchemaError as err:
        print("SchemaError during record validation! %s" % err)


def delete_record(recid):
    print("Deleting record ", recid)
    uuid = PersistentIdentifier.query.filter_by(pid_value=recid).first().object_uuid
    r = Record.get_record(uuid)
    r.delete()
    db.session.commit()


delete_duplicates(find_duplicates_dois())
