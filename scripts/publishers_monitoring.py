from datetime import datetime

from dateutil.relativedelta import relativedelta
from inspire_utils.record import get_value
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_files.api import Record
from invenio_search import current_search_client as es

# need to run in old scoap3 pod


def get_date_str(time_unit):
    if time_unit == "h":
        return "hours"
    if time_unit == "d":
        return "days"
    if time_unit == "w":
        return "weeks"
    if time_unit == "m":
        return "months"
    if time_unit == "y":
        return "years"


time_unit = input("Enter time unit, one of possible options: h, d, w, m, y \n")
if not time_unit:
    time_unit = "y"
gte = int(input("Search " + get_date_str(time_unit) + "ago: \n"))
if not gte:
    gte = 1
action = input("Records  _updated or _created? \n")
if not action:
    action = "_updated"


def get_all_records_recids():
    query = {
        "query": {
            "range": {
                action: {
                    "gte": "now-" + gte + time_unit + "/" + time_unit,
                    "lt": "now/" + time_unit,
                }
            }
        }
    }

    page = es.search(index="scoap3-records-record", scroll="1m", body=query)
    sid = page["_scroll_id"]
    scroll_size = len(page["hits"]["hits"])
    recids = {}
    while scroll_size > 0:
        for record_index in range(scroll_size):
            recids.append(
                get_value(
                    page["hits"]["hits"][record_index], "_source.control_number", ""
                )
            )
        page = es.scroll(scroll_id=sid, scroll="2m")
        sid = page["_scroll_id"]
        scroll_size = len(page["hits"]["hits"])

    return recids


def get_files_versions(recids):
    dois_and_files = {}
    for recid in recids:
        pid = PersistentIdentifier.get("recid", recid)
        existing_record = Record.get_record(pid.object_uuid)
        doi = existing_record["dois"][0]["value"]
        if doi not in dois_and_files:
            dois_and_files[doi] = {}
        for file_obj in existing_record.files:
            file_data = {}
            bucket = file_obj.data["bucket"]
            filetype = file_obj.data["filetype"]
            key = file_obj.data["key"]
            file_data["filetype"] = filetype
            file_data["all_versions"] = {
                version: version.created
                for version in file_obj.get_versions(bucket=bucket, key=key).all()
            }
            file_data["head_version"] = file_obj.obj.get(bucket=bucket, key=key)
            dois_and_files[doi][filetype] = file_data
    return dois_and_files


def get_date(gte, time_unit):
    current_datetime = datetime.now()
    if time_unit == "h":
        return current_datetime - relativedelta(hours=gte)
    if time_unit == "d":
        return current_datetime - relativedelta(days=gte)
    if time_unit == "w":
        return current_datetime - relativedelta(weeks=gte)
    if time_unit == "m":
        return current_datetime - relativedelta(months=gte)
    if time_unit == "y":
        return current_datetime - relativedelta(years=gte)


def get_only_updated_files(dois_and_files):
    updated = {}
    created = {}
    query_date = get_date(gte, time_unit)
    for doi in dois_and_files:
        if doi not in updated:
            updated[doi] = {}
        for file_type in dois_and_files[doi]:
            head_version = dois_and_files[doi][file_type]["head_version"]
            date_of_head_version = dois_and_files[doi][file_type]["all_versions"][
                head_version
            ]
            if len(dois_and_files[doi][file_type]["all_versions"]) == 1:
                created[doi][file_type] = date_of_head_version
            if date_of_head_version >= query_date:
                if doi not in created:
                    created[doi] = {}
                created[doi][file_type] = date_of_head_version
    return {"updated": updated, "created": created}
