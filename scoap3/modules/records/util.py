# -*- coding: utf-8 -*-
#
# This file is part of INSPIRE.
# Copyright (C) 2016 CERN.
#
# INSPIRE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INSPIRE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with INSPIRE. If not, see <http://www.gnu.org/licenses/>.
#
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

"""Helpers for handling records."""
import copy
import re

from flask import current_app
from inspire_utils.record import get_value
from invenio_db import db
from invenio_search import current_search_client
from invenio_workflows import workflow_object_class
from invenio_workflows.tasks import start

from scoap3.utils.arxiv import clean_arxiv

SPLIT_KEY_PATTERN = re.compile(r'\.|\[')


def get_title(record):
    """Get preferred title from record."""
    title = ""
    for title in record.get('titles', []):
        if title.get('title'):
            return title['title']

    return title


def get_first_publisher(record):
    return record['imprints'][0]['publisher']


def get_first_journal(record):
    return record['publication_info'][0]['journal_title']


def get_first_arxiv(record):
    return clean_arxiv(get_value(record, 'arxiv_eprints.value[0]'))


def get_first_doi(record):
    return record['dois'][0]['value']


def get_abbreviated_publisher(record):
    """Returns abbreviated publisher name, or the original one if abbreviation doesn't exists"""
    publisher = get_first_publisher(record)
    return current_app.config.get('PUBLISHER_ABBREVIATIONS').get(publisher, publisher)


def get_abbreviated_journal(record):
    """Returns abbreviated publisher name, or the original one if abbreviation doesn't exists"""
    journal = get_first_journal(record)
    return current_app.config.get('JOURNAL_ABBREVIATIONS').get(journal, journal)


def get_arxiv_primary_category(record):
    """Return primary arXiv category for record. None if not available."""
    return get_value(record, 'arxiv_eprints[0].categories[0]')


def create_from_json(records, apply_async=True):
    current_app.logger.info('Loading dump...')

    results = []

    for i, record in enumerate(records['records']):
        obj = workflow_object_class.create(data=record)
        extra_data = {}
        record_extra = record.pop('extra_data', {})
        if record_extra:
            extra_data['record_extra'] = record_extra

        obj.extra_data['source_data'] = {
            'data': copy.deepcopy(record),
            'extra_data': copy.deepcopy(extra_data),
        }
        obj.extra_data.update(extra_data)

        obj.data_type = current_app.config['CRAWLER_DATA_TYPE']
        obj.save()
        db.session.commit()

        queue = current_app.config['CRAWLER_CELERY_QUEUE']

        if apply_async:
            workflow = start.apply_async(
                kwargs={
                    'workflow_name': "articles_upload",
                    'object_id': obj.id,
                },
                queue=queue,
            )
        else:
            workflow = start(workflow_name="articles_upload", object_id=obj.id)
        results.append(workflow)

        current_app.logger.info('Parsed record {}.'.format(i))

    return results


def is_doi_in_db(doi):
    return current_search_client.count(q='dois.value:"%s"' % doi)['count'] > 0
