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
import logging
from StringIO import StringIO

from datetime import datetime
from flask import url_for, current_app
from inspire_dojson.utils import strip_empty_values
from inspire_schemas.utils import validate
from inspire_utils.record import get_value

from invenio_db import db
from invenio_files_rest.models import Bucket
from invenio_mail.api import TemplatedMessage
from invenio_oaiserver.minters import oaiid_minter
from invenio_pidstore.errors import PIDAlreadyExists
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_files.api import Record
from invenio_records_files.models import RecordsBuckets
from invenio_search import current_search_client as es

from jsonschema.exceptions import ValidationError, SchemaError

from scoap3.modules.compliance.compliance import check_compliance
from scoap3.modules.pidstore.minters import scoap3_recid_minter
from scoap3.modules.records.util import is_doi_in_db
from scoap3.utils.arxiv import get_arxiv_categories
from scoap3.utils.nations import find_country

from workflow.patterns.controlflow import IF_ELSE

from scoap3.utils.http import requests_retry_session

logger = logging.getLogger(__name__)


def __halt_and_notify(msg, eng):
    ctx = {
        'reason': msg,
        'url': url_for('workflow.details_view', id=eng.model.uuid, _external=True)
    }

    template_msg = TemplatedMessage(
        template_html='scoap3_workflows/emails/halted_article_upload.html',
        subject='SCOAP3 - Artcile upload halted',
        sender=current_app.config.get('MAIL_DEFAULT_SENDER'),
        recipients=current_app.config.get('ADMIN_DEFAULT_EMAILS'),
        ctx=ctx
    )
    current_app.extensions['mail'].send(template_msg)

    eng.halt(msg)


def get_first_doi(obj):
    return get_value(obj.data, 'dois[0].value')


def set_schema(obj, eng):
    """Make sure schema is set properly and resolve it."""
    obj.data['$schema'] = url_for('invenio_jsonschemas.get_schema', schema_path="hep.json")


def add_arxiv_category(obj, eng):
    """Add arXiv categories fetched from arXiv.org"""
    if "arxiv_eprints" in obj.data:
        for element in obj.data.get("arxiv_eprints", ()):
            if 'value' not in element:
                logger.warning('arxiv_eprints value missing for article with doi: %s' % get_first_doi(obj))
                continue

            arxiv_id = element['value']

            if 'categories' not in element:
                categories = get_arxiv_categories(arxiv_id)
                element['categories'] = categories


def add_nations(obj, eng):
    """Add nations extracted from affiliations"""
    if 'authors' not in obj.data:
        __halt_and_notify('No authors for article.', eng)

    for author_index, author in enumerate(obj.data['authors']):
        if 'affiliations' not in author:
            __halt_and_notify('No affiliations for author: %s.' % author, eng)

        for affiliation_index, affiliation in enumerate(author['affiliations']):
            obj.data['authors'][author_index]['affiliations'][affiliation_index]['country'] = find_country(
                affiliation['value'])


def remove_orcid_prefix(obj, eng):
    orcid_prefixes = ('orcid:', 'https://orcid.org/', 'http://orcid.org/')
    for author in obj.data.get('authors', ()):
        for orcid_prefix in orcid_prefixes:
            if 'orcid' in author and author['orcid'].lower().startswith(orcid_prefix):
                author['orcid'] = author['orcid'][len(orcid_prefix):]


def delete_unwanted_fields(obj, eng):
    """Delete unwanted fields"""

    keys_to_delete = (
        "curated",
        "citeable",
        "files",
    )

    for key in keys_to_delete:
        obj.data.pop(key, None)


def delete_empty_fields(obj, eng):
    obj.data = strip_empty_values(obj.data)


def is_record_in_db(obj, eng):
    """Checks if record is in database"""
    return is_doi_in_db(get_first_doi(obj))


def set_springer_source_if_needed(obj):
    text = 'Italiana di Fisica'.lower()
    if ('abstracts' in obj.data and
            'source' in obj.data['abstracts'][0] and
            text in obj.data['abstracts'][0]['source'].lower()):
        obj.data['abstracts'][0]['source'] = 'Springer/SIF'

    if 'acquisition_source' in obj.data and text in obj.data['acquisition_source']['source'].lower():
        obj.data['acquisition_source']['source'] = 'Springer/SIF'


def store_record(obj, eng):
    """Stores record in database"""
    set_springer_source_if_needed(obj)

    try:
        record = Record.create(obj.data, id_=None)

        # Create persistent identifier.
        scoap3_recid_minter(str(record.id), record)
        obj.save()
        record.commit()

        # Commit to DB before indexing
        db.session.commit()
        obj.data['control_number'] = record['control_number']
        obj.save()

    except ValidationError as err:
        __halt_and_notify("Validation error: %s." % err, eng)

    except PIDAlreadyExists:
        __halt_and_notify("Record with this id already in DB", eng)
        # updating deleted record
        # pid = PersistentIdentifier.get('recid', record['control_number'])
        # pid.assign('rec', record.id, overwrite=True)


def update_record(obj, eng):
    """Updates existing record"""

    doi = get_first_doi(obj)

    query = {'query': {'bool': {'must': [{'match': {'dois.value': doi}}], }}}
    search_result = es.search(index='scoap3-records-record', body=query)

    recid = search_result['hits']['hits'][0]['_source']['control_number']

    obj.extra_data['recid'] = recid
    obj.data['control_number'] = recid

    pid = PersistentIdentifier.get('recid', recid)
    existing_record = Record.get_record(pid.object_uuid)

    if '_files' in existing_record:
        obj.data['_files'] = existing_record['_files']
    if '_oai' in existing_record:
        obj.data['_oai'] = existing_record['_oai']

    # preserving original creation date
    creation_date = existing_record['record_creation_date']
    obj.data['record_creation_date'] = creation_date
    existing_record.clear()
    existing_record.update(obj.data)

    try:
        existing_record.commit()
        obj.save()
        db.session.commit()
    except ValidationError as err:
        __halt_and_notify("Validation error: %s." % err, eng)
    except SchemaError as err:
        __halt_and_notify('SchemaError during record validation! %s' % err, eng)


def __extract_local_files_info(obj, doi):
    files = []
    if 'local_files' not in obj.data:
        return files

    for local_file in obj.data.pop('local_files'):
        if local_file['value']['filetype'] in ['pdf/a', 'pdfa']:
            files.append(
                {'url': local_file['value']['path'],
                 'name': '{0}_a.{1}'.format(doi, 'pdf'),
                 'filetype': 'pdf/a'}
            )
        else:
            files.append(
                {'url': local_file['value']['path'],
                 'name': '{0}.{1}'.format(doi, local_file['value']['filetype']),
                 'filetype': local_file['value']['filetype']}
            )

    return files


def build_files_data(obj, eng):
    doi = get_first_doi(obj)
    method = obj.data['acquisition_source']['method']

    if method == 'APS':
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
    elif 'Hindawi' in method:
        doi_part = doi.split('10.1155/')[1]
        obj.extra_data['files'] = [
            {'url': 'http://downloads.hindawi.com/journals/ahep/{0}.pdf'.format(doi_part),
             'name': '{0}.pdf'.format(doi),
             'filetype': 'pdf'},
            {'url': 'http://downloads.hindawi.com/journals/ahep/{0}.xml'.format(doi_part),
             'name': '{0}.xml'.format(doi),
             'filetype': 'xml'}
        ]
    elif method == 'scoap3_push':
        files = []
        for document in obj.data.pop('documents', ()):
            known_extensions = ('xml', 'pdfa', 'pdf')

            ext = None
            for known_ext in known_extensions:
                if known_ext in document['key']:
                    ext = known_ext

            if ext not in known_extensions:
                __halt_and_notify('Invalid file type: %s' % document['key'], eng)

            files.append(
                {
                    'url': document['url'],
                    'name': doi,
                    'filetype': ext
                }
            )
        obj.extra_data['files'] = files
    else:
        obj.extra_data['files'] = __extract_local_files_info(obj, doi)

    obj.save()


def attach_files(obj, eng):
    if 'files' in obj.extra_data:
        recid = obj.data['control_number']
        pid = PersistentIdentifier.get('recid', recid)
        existing_record = Record.get_record(pid.object_uuid)

        if '_files' not in existing_record or not existing_record['_files']:
            bucket = Bucket.create()
            RecordsBuckets.create(record=existing_record.model, bucket=bucket)

        for file_ in obj.extra_data['files']:
            if file_['url'].startswith('http'):
                data = requests_retry_session().get(file_['url'], headers=file_.get('headers', {}))
                f = StringIO(data.content)
            else:
                f = open(file_['url'])

            existing_record.files[file_['name']] = f
            existing_record.files[file_['name']]['filetype'] = file_['filetype']

        obj.save()
        existing_record.commit()
        db.session.commit()
    else:
        __halt_and_notify('No files found.', eng)


def _get_oai_sets(record):
    for phrase, set_name in current_app.config.get('JOURNAL_ABBREVIATIONS').iteritems():
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
        current_app.logger.info('adding new oai id')
        oaiid_minter(pid.object_uuid, existing_record)

    if 'sets' not in existing_record['_oai'] or not existing_record['_oai']['sets']:
        existing_record['_oai']['sets'] = _get_oai_sets(existing_record)

    existing_record['_oai']['updated'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

    existing_record.commit()
    obj.save()
    db.session.commit()


def validate_record(obj, eng):
    """
    Validate record based on its schema.

    If there is no schema or the record is invalid, the workflow will be halted.
    """

    if '$schema' not in obj.data:
        __halt_and_notify('No schema found!', eng)
        return

    schema_data = requests_retry_session().get(obj.data['$schema']).content
    schema_data = json.loads(schema_data)

    try:
        validate(obj.data, schema_data)
    except ValidationError as err:
        __halt_and_notify('Invalid record: %s' % err, eng)
    except SchemaError as err:
        __halt_and_notify('SchemaError during record validation! %s' % err, eng)


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


class ArticlesUpload(object):
    """Article ingestion workflow for Records collection."""
    name = "HEP"
    data_type = "harvesting"
    workflow = [
        set_schema,
        add_arxiv_category,
        add_nations,
        remove_orcid_prefix,
        delete_unwanted_fields,
        delete_empty_fields,
        build_files_data,
        STORE_REC,
        attach_files,
        add_oai_information,
        check_compliance,
        validate_record,
    ]
