# -*- coding: utf-8 -*-
#
# This file is part of SCOAP3.
# Copyright (C) 2016 CERN.
#
# SCOAP3 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SCOAP3 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SCOAP3. If not, see <http://www.gnu.org/licenses/>.
#
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

"""Workflow for processing single records harvested"""

from __future__ import absolute_import, division, print_function
from flask import url_for
from datetime import datetime
from urllib2 import urlopen
import urllib2

from workflow.patterns.controlflow import (
    IF,
    IF_ELSE,
    IF_NOT,
)

from invenio_db import db
from invenio_files_rest.models import Bucket
from invenio_records_files.api import Record
from invenio_records_files.models import RecordsBuckets  
from invenio_pidstore.models import PersistentIdentifier
from invenio_search import current_search_client as es
from invenio_indexer.api import RecordIndexer

from invenio_pidstore.errors import PIDAlreadyExists
from scoap3.modules.pidstore.minters import scoap3_recid_minter
from jsonschema.exceptions import ValidationError

def set_schema(obj, eng):
    """Make sure schema is set properly and resolve it."""
    obj.data['$schema'] = url_for('invenio_jsonschemas.get_schema', schema_path="hep.json")
    # if '$schema' not in obj.data:
    #     obj.data['$schema'] = "{data_type}.json".format(
    #         data_type=obj.data_type or eng.workflow_definition.data_type
    #     )

    # if not obj.data['$schema'].startswith('http'):
    #     obj.data['$schema'] = url_for(
    #         'invenio_jsonschemas.get_schema',
    #         schema_path="records/{0}".format(obj.data['$schema'])
    #     )

def record_not_published_before_2014(obj, eng):
    """Make sure record was published in 2014 and onwards."""
    try:
        datetime_object = datetime.strptime(obj.data['imprints'][0]['date'], '%Y-%m-%d')
    except:
        datetime_object = datetime.strptime(obj.data['imprints'][0]['date'], '%Y-%m')
    if not datetime_object.year >= 2014:
        eng.halt("Record published before 2014")
    return True

def is_record_from_partial_journal(obj, eng):
    """Check if record comes from journal partially funded by SCOAP3."""
    partial_journals = ["Acta Physica Polonica B",
                        "Chinese Physics C",
                        "Journal of Cosmology and Astroparticle Physics",
                        "New Journal of Physics",
                        "Progress of Theoretical and Experimental Physics"]
    if obj.data['publication_info'][0]['journal_title'] in partial_journals:
        return True
    else:
        return False

def add_arxiv_category(obj, eng):
    """Add arXiv categories fetched from arXiv.org"""
    from scoap3.utils.arxiv import get_arxiv_categories
    if "arxiv_eprints" in obj.data:
        for i, arxiv_id in enumerate(obj.data["arxiv_eprints"]):
            if arxiv_id['value'].startswith("arXiv:"):
                arxiv_id = arxiv_id['value'][6:].split('v')[0]
            arxiv_id = arxiv_id.split('v')[0]
            categories = get_arxiv_categories(arxiv_id)
            obj.data["arxiv_eprints"][i]['categories'] = categories

def check_arxiv_category(obj, eng):
    """Check if at least one arXiv category is in SCOAP3_REQUIRED_ARXIV_CATEGORIES"""
    # TODO move this list to config variable SCOAP3_REQUIRED_ARXIV_CATEGORIES
    arxiv_hep_categories = set(["hep-ex","hep-lat","hep-ph","hep-th"])
    if "arxiv_eprints" in obj.data:
        for arxiv_id in obj.data["arxiv_eprints"]:
            if not set(arxiv_id['categories']).intersection(arxiv_hep_categories):
                eng.halt("It is a paper from partial journal, but it doesn't have correct arXiv category!")
    else:
        eng.halt(action='add_arxiv',
                 msg="Missing arXiv id - you need to ad it to proceed.")

def add_nations(obj, eng):
    """Add nations extracted from affiliations"""
    from scoap3.dojson.utils.nations import find_nation
    for author_index, author in enumerate(obj.data.get('authors', [])):
        for affiliation_index, affiliation in enumerate(author.get('affiliations',[])):
            obj.data['authors'][author_index]['affiliations'][affiliation_index]['country'] = find_nation(affiliation['value'])

def emit_record_signals(obj, eng):
    """Emit record signals to update record metadata."""
    from scoap3_records.signals import before_record_insert
    before_record_insert.send(obj.data)

def is_record_in_db(obj, eng):
    """Checks if record is in database"""
    doi_count = es.count(q='dois.value:"%s"' % (obj.data['dois'][0]['value'],))['count']
    if doi_count:
       return True
    else:
       return False

def store_record(obj, eng):
    """Stores record in database"""
    try:
        record = Record.create(obj.data, id_=None)
    except ValidationError as err:
        eng.halt("Validation error: %s. Skipping..." % (err,))
    # Create persistent identifier.
    try:
        pid = scoap3_recid_minter(str(record.id), record)
    except PIDAlreadyExists:
        eng.halt("Record with this id already in DB")
    # Commit any changes to record
    record.commit()
    # Commit to DB before indexing
    db.session.commit()
    obj.data['control_number'] = record['control_number']
    # Index record
    indexer = RecordIndexer()
    indexer.index_by_id(pid.object_uuid)

def update_record(obj, eng):
    """Updates existing record"""
    doi = obj.data.get('dois')[0]
    doi = doi['value']

    query = {'query': {'bool': {'must': [{'match': {'dois.value': doi}}],}}}
    search_result = es.search(index='records-record', doc_type='record-v1.0.0', body=query)

    recid = search_result['hits']['hits'][0]['_source']['control_number']

    obj.extra_data['recid'] = recid
    obj.data['control_number']= recid

    pid = PersistentIdentifier.get('recid', recid)
    existing_record = Record.get_record(pid.object_uuid)

    if '_files' in existing_record:
        obj.data['_files'] = existing_record['_files']
    existing_record.clear()
    existing_record.update(obj.data)
    print(obj.data)
    print(existing_record)
    existing_record.commit()
    obj.save()

    db.session.commit()

def add_to_before_2014_collection(obj, eng):
    """Adds record to collection of atricles published before 2014"""
    obj.data['collections'].append({"primary":"before_2014"})

def _get_oai_sets(record):
    if 'Phys. Rev. D' in record['publication_info'][0]['journal_title']:
        return ['PRD']
    if 'Phys. Rev. Lett' in record['publication_info'][0]['journal_title']:
        return ['PRC']
    if 'Phys. Rev. Lett' in record['publication_info'][0]['journal_title']:
        return ['PRL']

def add_oai_information(obj, eng):
    """Adds OAI information like identifier"""
    from invenio_oaiserver.minters import oaiid_minter

    recid = obj.data['control_number']
    pid = PersistentIdentifier.get('recid', recid)

    existing_record = Record.get_record(pid.object_uuid)

    if '_oai' not in existing_record:
        try:
            oaiid_minter(pid.object_uuid, existing_record)
        except PIDAlreadyExists:
            existing_record['_oai'] = {
                'id': 'oai:beta.scoap3.org:' + recid,
                'sets': _get_oai_sets(existing_record)
            }

    if 'id' not in existing_record['_oai']:
        oaiid_minter(pid.object_uuid, existing_record)
    if 'sets' not in existing_record['_oai']:
        existing_record['_oai']['sets'] = _get_oai_sets(existing_record)
    elif existing_record['_oai']['sets'] == None:
        existing_record['_oai']['sets'] = _get_oai_sets(existing_record)

    existing_record['_oai']['updated'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    #existing_record['_oai']['updated'] = datetime.utcnow().isoformat()

    existing_record.commit()
    obj.save()
    db.session.commit()
    indexer = RecordIndexer()
    indexer.index_by_id(pid.object_uuid)

def attach_files(obj, eng):
    if 'files' in obj.extra_data:
        recid = obj.data['control_number']
        pid = PersistentIdentifier.get('recid', recid)
        existing_record = Record.get_record(pid.object_uuid)

        bucket = Bucket.create()
        record_buckets = RecordsBuckets.create(record=existing_record.model, bucket=bucket)

        for file_ in obj.extra_data['files']:
            request = urllib2.Request(file_['url'], headers=file_.get('headers',None))
            f = urllib2.urlopen(request)
            existing_record.files[file_['name']] = f
            existing_record.files[file_['name']]['filetype'] = file_['filetype']

        obj.save()
        existing_record.commit()
        db.session.commit()

def update_files(obj, eng):
    pass
    # recid = obj.data['control_number']
    # pid = PersistentIdentifier.get('recid', recid)
    # existing_record = Record.get_record(pid.object_uuid)


def build_files_data(obj, eng):
    doi = obj.data.get('dois')[0]['value']
    if obj.data['acquisition_source']['source'] == 'APS':
        obj.extra_data['files'] = [
            {'url':'http://harvest.aps.org/v2/journals/articles/{0}'.format(doi),
             'headers':{'Accept':'application/pdf'},
             'name':'{0}.pdf'.format(doi),
             'filetype':'pdf'},
            {'url':'http://harvest.aps.org/v2/journals/articles/{0}'.format(doi),
             'headers':{'Accept':'text/xml'},
             'name':'{0}.xml'.format(doi),
             'filetype':'xml'}
        ]
    if obj.data['acquisition_source']['source'] == 'Hindawi':
        doi_part = doi.split('10.1155/')[1]
        obj.extra_data['files'] = [
            {'url':'http://downloads.hindawi.com/journals/ahep/{0}.pdf'.format(doi_part),
             'name':'{0}.pdf'.format(doi),
             'type':'pdf'},
            {'url':'http://downloads.hindawi.com/journals/ahep/{0}.xml'.format(doi_part),
             'name':'{0}.xml'.format(doi),
             'type':'xml'}
        ]
    obj.save()

def are_files_attached(obj, eng):
    recid = obj.data['control_number']
    pid = PersistentIdentifier.get('recid', recid)
    existing_record = Record.get_record(pid.object_uuid)
    if '_files' in existing_record:
        if existing_record['_files']:
            return True
    return False

def are_files_new(obj, eng):
    pass
    # import urllib2
    # from tempfile import mkstemp

    # if 'files' in obj.extra_data:
    #     for file_ in obj.extra_data['files']:
    #         request = urllib2.Request(file_['url'], headers=file_['headers'])
    #         tmp_file = mkstemp(suffix='_workflow_file_{0}'.format(file_['name']))
    #         f = open(tmp_file[1],'w')
    #         f.write(urllib2.urlopen(request).read())

    #         obj.


    #     request = urllib2.Request("http://harvest.aps.org/v2/journals/articles/{0}".format(doi), headers={"Accept" : "application/pdf"})
    #         pdf = urllib2.urlopen(request).read()
    #         try:
    #             pdf_file = mkstemp(suffix='_aps_file')
    #             f = open(pdf_file[1],'w')
    #             f.write(pdf)
    #             f.close()
    #         except:
    #             write_message(traceback.print_exc())



PART1 = [
        IF_ELSE(
            record_not_published_before_2014,
            [
                IF(
                    is_record_from_partial_journal,
                    [
                        check_arxiv_category,
                    ]
                ),
            ],
            [
                add_to_before_2014_collection,
            ]
        ),
]

STORE_REC = [
        IF_ELSE(
            is_record_in_db,
            [
                update_record,
            ],
            [
                store_record,
            ]
        ),
]

FILES = [
        build_files_data,
        IF_ELSE(
            are_files_attached,
            [
                IF(
                    are_files_new,
                    [
                        update_files,
                    ]
                )
            ],
            [
                attach_files,
            ]
        )
]

class ArticlesUpload(object):
    """Article ingestion workflow for Records collection."""
    name = "HEP"
    data_type = "harvesting"

    workflow = [
        set_schema,
        add_arxiv_category,
        PART1,
        add_nations,
        STORE_REC,
        FILES,
        add_oai_information
    ]


