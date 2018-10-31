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

import json
import urllib2

from datetime import datetime
from flask import url_for, current_app

from invenio_db import db
from invenio_files_rest.models import Bucket
from invenio_indexer.api import RecordIndexer
from invenio_oaiserver.minters import oaiid_minter
from invenio_pidstore.errors import PIDAlreadyExists
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_files.api import Record
from invenio_records_files.models import RecordsBuckets
from invenio_search import current_search_client as es

from jsonschema import validate
from jsonschema.exceptions import ValidationError, SchemaError

from scoap3.dojson.utils.nations import find_nation
from scoap3.modules.compliance.compliance import check_compliance
from scoap3.modules.pidstore.minters import scoap3_recid_minter
from scoap3.utils.arxiv import get_arxiv_categories, get_arxiv_primary_category

from workflow.patterns.controlflow import IF_ELSE


def validate_schema(obj, eng):
    schema_url = urllib2.urlopen(obj.data['$schema'])
    schema = json.loads(schema_url.read())
    try:
        validate(obj.data, schema)
    except ValidationError as err:
        eng.halt("{0}".format(err))
    except SchemaError as err:
        eng.halt("{0}".format(err))


def set_schema(obj, eng):
    """Make sure schema is set properly and resolve it."""
    obj.data['$schema'] = url_for('invenio_jsonschemas.get_schema', schema_path="hep.json")


def add_arxiv_category(obj, eng):
    """Add arXiv categories fetched from arXiv.org"""
    if "report_numbers" in obj.data:
        for i, arxiv_id in enumerate(obj.data["report_numbers"]):
            if arxiv_id['value'].lower().startswith("arxiv:"):
                arxiv_id = arxiv_id['value'][6:].split('v')[0]
            arxiv_id = arxiv_id.split('v')[0]

            categories = get_arxiv_categories(arxiv_id)
            obj.data["report_numbers"][i]['categories'] = categories

            primary_category = get_arxiv_primary_category(arxiv_id)
            obj.data["report_numbers"][i]['primary_category'] = primary_category


def add_nations(obj, eng):
    """Add nations extracted from affiliations"""
    for author_index, author in enumerate(obj.data.get('authors', [])):
        for affiliation_index, affiliation in enumerate(author.get('affiliations',[])):
            obj.data['authors'][author_index]['affiliations'][affiliation_index]['country'] = find_nation(affiliation['value'])


def is_record_in_db(obj, eng):
    """Checks if record is in database"""
    doi_count = es.count(q='dois.value:"%s"' % (obj.data['dois'][0]['value'],))['count']
    if doi_count:
        return True
    else:
        return False


def store_record(obj, eng):
    """Stores record in database"""
    if 'Italiana di Fisica'.lower() in obj.data['abstracts'][0]['source'].lower():
        obj.data['abstracts'][0]['source'] = 'Springer/SIF'
    if 'Italiana di Fisica'.lower() in obj.data['acquisition_source']['source'].lower():
        obj.data['acquisition_source']['source'] = 'Springer/SIF'
    try:
        record = Record.create(obj.data, id_=None)
    except ValidationError as err:
        eng.halt("Validation error: %s. Skipping..." % (err,))
    # Create persistent identifier.
    try:
        pid = scoap3_recid_minter(str(record.id), record)
    except PIDAlreadyExists:
        eng.halt("Record with this id already in DB")
        # updating deleted record
        # pid = PersistentIdentifier.get('recid', record['control_number'])
        # pid.assign('rec', record.id, overwrite=True)
    # Commit any changes to record
    obj.save()
    record.commit()
    # Commit to DB before indexing
    db.session.commit()
    obj.data['control_number'] = record['control_number']
    obj.save()
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
    obj.data['control_number'] = recid

    pid = PersistentIdentifier.get('recid', recid)
    existing_record = Record.get_record(pid.object_uuid)

    if '_files' in existing_record:
        obj.data['_files'] = existing_record['_files']
    if '_oai' in existing_record:
        obj.data['_oai'] = existing_record['_oai']
    if 'Italiana di Fisica'.lower() in obj.data['abstracts'][0]['source'].lower():
        obj.data['abstracts'][0]['source'] = 'Springer/SIF'
    if 'Italiana di Fisica'.lower() in obj.data['acquisition_source']['source'].lower():
        obj.data['acquisition_source']['source'] = 'Springer/SIF'

    # preserving oryginal creation date
    obj.data['record_creation_date'] = existing_record['record_creation_date']
    existing_record.clear()
    existing_record.update(obj.data)
    existing_record.commit()
    obj.save()
    db.session.commit()


def add_to_before_2014_collection(obj, eng):
    """Adds record to collection of atricles published before 2014"""
    obj.data['collections'].append({"primary":"before_2014"})


def _get_oai_sets(record):
    for phrase, set_name in current_app.config.get('JOURNAL_TITLE_ABREVIATION').iteritems():
        if phrase in record['publication_info'][0]['journal_title']:
            return [set_name]
    return []


def add_oai_information(obj, eng):
    """Adds OAI information like identifier"""
    recid = obj.data['control_number']
    pid = PersistentIdentifier.get('recid', recid)
    existing_record = Record.get_record(pid.object_uuid)

    if '_oai' not in existing_record:
        try:
            oaiid_minter(pid.object_uuid, existing_record)
        except PIDAlreadyExists:
            existing_record['_oai'] = {
                'id': 'oai:beta.scoap3.org:%s' % recid,
                'sets': _get_oai_sets(existing_record)
            }
    if 'id' not in existing_record['_oai']:
        print('adding new oai id')
        oaiid_minter(pid.object_uuid, existing_record)
    if 'sets' not in existing_record['_oai']:
        existing_record['_oai']['sets'] = _get_oai_sets(existing_record)
    elif not existing_record['_oai']['sets']:
        existing_record['_oai']['sets'] = _get_oai_sets(existing_record)

    existing_record['_oai']['updated'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    existing_record.commit()
    obj.save()
    db.session.commit()
    indexer = RecordIndexer()
    indexer.index_by_id(pid.object_uuid)


def attach_files(obj, eng):
    def are_files_attached(existing_record):
        if '_files' in existing_record and existing_record['_files']:
            return True
        return False

    if 'files' in obj.extra_data:
        recid = obj.data['control_number']
        pid = PersistentIdentifier.get('recid', recid)
        existing_record = Record.get_record(pid.object_uuid)

        if not are_files_attached(existing_record):
            bucket = Bucket.create()
            record_buckets = RecordsBuckets.create(record=existing_record.model, bucket=bucket)

        for file_ in obj.extra_data['files']:
            if file_['url'].startswith('http'):
                request = urllib2.Request(file_['url'], headers=file_.get('headers',{}))
                f = urllib2.urlopen(request)
            else:
                f = open(file_['url'])
            existing_record.files[file_['name']] = f
            existing_record.files[file_['name']]['filetype'] = file_['filetype']

        obj.save()
        existing_record.commit()
        db.session.commit()


def build_files_data(obj, eng):
    doi = obj.data.get('dois')[0]['value']
    if obj.data['acquisition_source']['method'] == 'APS':
        obj.extra_data['files'] = [
            {'url': 'http://harvest.aps.org/v2/journals/articles/{0}'.format(doi),
             'headers': {'Accept': 'application/pdf'},
             'name': '{0}.pdf'.format(doi),
             'filetype': 'pdf'},
            {'url': 'http://harvest.aps.org/v2/journals/articles/{0}'.format(doi),
             'headers': {'Accept': 'text/xml'},
             'name': '{0}.xml'.format(doi),
             'filetype': 'xml'}
        ]
    if obj.data['acquisition_source']['method'] == 'Hindawi':
        doi_part = doi.split('10.1155/')[1]
        obj.extra_data['files'] = [
            {'url': 'http://downloads.hindawi.com/journals/ahep/{0}.pdf'.format(doi_part),
             'name': '{0}.pdf'.format(doi),
             'filetype': 'pdf'},
            {'url': 'http://downloads.hindawi.com/journals/ahep/{0}.xml'.format(doi_part),
             'name': '{0}.xml'.format(doi),
             'filetype': 'xml'}
        ]
    if obj.data['acquisition_source']['method'] in ['Elsevier', 'Springer', 'Oxford University Press', 'scoap3']:
        obj.extra_data['files'] = _extract_local_files_info(obj, doi)
        #remove local files from data
        del(obj.data['local_files'])
    obj.save()


def are_files_attached(obj, eng):
    recid = obj.data['control_number']
    pid = PersistentIdentifier.get('recid', recid)
    existing_record = Record.get_record(pid.object_uuid)
    if '_files' in existing_record:
        if existing_record['_files']:
            return True
    return False


def _extract_local_files_info(obj, doi):
    f = []
    if 'local_files' in obj.data:
        for local_file in obj.data['local_files']:
            if local_file['value']['filetype'] in ['pdf/a', 'pdfa']:
                f.append(
                    {'url': local_file['value']['path'],
                     'name': '{0}_a.{1}'.format(doi, 'pdf'),
                     'filetype': 'pdf/a'}
                )
            else:
                f.append(
                    {'url': local_file['value']['path'],
                     'name': '{0}.{1}'.format(doi, local_file['value']['filetype']),
                     'filetype': local_file['value']['filetype']}
                )

    return f

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
        attach_files,
]


class ArticlesUpload(object):
    """Article ingestion workflow for Records collection."""
    name = "HEP"
    data_type = "harvesting"

    workflow = [
        set_schema,
        add_arxiv_category,
        add_nations,
        STORE_REC,
        FILES,
        add_oai_information,
        check_compliance,
    ]
