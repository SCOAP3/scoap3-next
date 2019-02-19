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
from uuid import uuid1

from flask import current_app
from inspire_crawler.models import CrawlerWorkflowObject
from invenio_db import db
from invenio_workflows import WorkflowEngine, workflow_object_class
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
    for arxiv in record.get('arxiv_eprints', ()):
        if 'value' in arxiv:
            return clean_arxiv(arxiv['value'])
    return None


def get_first_doi(record):
    return record['dois'][0]['value']


def get_value(record, key, default=None):
    """Return item as `dict.__getitem__` but using 'smart queries'.
    .. note::
        Accessing one value in a normal way, meaning d['a'], is almost as
        fast as accessing a regular dictionary. But using the special
        name convention is a bit slower than using the regular access:
        .. code-block:: python
            >>> %timeit x = dd['a[0].b']
            100000 loops, best of 3: 3.94 us per loop
            >>> %timeit x = dd['a'][0]['b']
            1000000 loops, best of 3: 598 ns per loop
    """
    def getitem(k, v):
        if isinstance(v, dict):
            return v[k]
        elif ']' in k:
            k = k[:-1].replace('n', '-1')
            # Work around for list indexes and slices
            try:
                return v[int(k)]
            except ValueError:
                return v[slice(*map(
                    lambda x: int(x.strip()) if x.strip() else None,
                    k.split(':')
                ))]
        else:
            tmp = []
            for inner_v in v:
                try:
                    tmp.append(getitem(k, inner_v))
                except KeyError:
                    continue
            return tmp

    # Check if we are using python regular keys
    try:
        return record[key]
    except KeyError:
        pass

    keys = SPLIT_KEY_PATTERN.split(key)
    value = record
    for k in keys:
        try:
            value = getitem(k, value)
        except KeyError:
            return default
    return value


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
    for arxiv_eprints in record.get('arxiv_eprints', ()):
        if 'categories' in arxiv_eprints and arxiv_eprints['categories']:
            return arxiv_eprints['categories'][0]

    return None


def create_from_json(records, apply_async=True):
    current_app.logger.info('Loading dump...')

    for i, record in enumerate(records['records']):
        engine = WorkflowEngine.with_name("articles_upload")
        engine.save()
        obj = workflow_object_class.create(data=record)
        obj.id_workflow = str(engine.uuid)
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

        job_id = uuid1()

        crawler_object = CrawlerWorkflowObject(
            job_id=job_id, object_id=obj.id
        )
        db.session.add(crawler_object)
        queue = current_app.config['CRAWLER_CELERY_QUEUE']

        if apply_async:
            start.apply_async(
                kwargs={
                    'workflow_name': "articles_upload",
                    'object_id': obj.id,
                },
                queue=queue,
            )
        else:
            start(workflow_name="articles_upload", object_id=obj.id)

        current_app.logger.info('Parsed record {}.'.format(i))
