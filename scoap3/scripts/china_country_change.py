 from invenio_search import current_search_client as es
 from invenio_pidstore.models import PersistentIdentifier
 from invenio_records_files.api import Record
 from invenio_db import db
 import re


 def get_cern_cooperation_agreement():
     records = {}
     query = {
         "_source": ["_files", "control_number", "dois"],
         "query": {
             "regexp": {
                 "authors.affiliations.value": {
                     "value": ".*Normal.*",
                     "flags": "ALL",
                     "case_insensitive": "true",
                 }
                 }
             }
         }

     search_result = es.search(index="scoap3-records-record", scroll='1m', body=query)
     sid = search_result['_scroll_id']
     scroll_size = len(search_result['hits']['hits'])
     while (scroll_size > 0):
         for record_index in range(scroll_size):
             recid = search_result["hits"]["hits"][record_index]["_source"]["control_number"]
             doi = search_result["hits"]["hits"][record_index]["_source"]["dois"][0]["value"]
             records[recid] = doi
         search_result = es.scroll(scroll_id=sid, scroll='2m')
         sid = search_result['_scroll_id']
         scroll_size = len(search_result['hits']['hits'])
     return records

 updated_records = {}
 def update_records(dois_and_recids):
         recids = dois_and_recids.keys()
         for recid in recids:
             flag = False
             pid = PersistentIdentifier.get("recid", recid)
             existing_record = Record.get_record(pid.object_uuid)
             for index_auth, author in enumerate(existing_record['authors']):
                 try:
                     for index_aff, affiliation in enumerate(existing_record['authors'][index_auth]['affiliations']):
                         if "South China Normal University" in affiliation['value']:
                             if existing_record['authors'][index_auth]['affiliations'][index_aff]['country'] == "Hong Kong":
                                 flag = True
                                 print("Country is " + existing_record['authors'][index_auth]['affiliations'][index_aff]['country'])
                                 existing_record['authors'][index_auth]['affiliations'][index_aff]['country'] = "China"
                                 print("Country should be " + existing_record['authors'][index_auth]['affiliations'][index_aff]['country'])
                         else:
                             pass
                 except:
                     pass
             if flag:
                 updated_records[dois_and_recids[recid]] = recid
                 print('Updating record...', recid)
                 existing_record.update(dict(existing_record))
                 existing_record.commit()
                 db.session.commit()