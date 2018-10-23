# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""Celery tasks used by SCOAP3 Analysis"""

from __future__ import absolute_import, print_function

from celery import shared_task
from invenio_search.api import current_search_client as es
from scoap3.modules.analysis.models import Gdp
from scoap3.modules.analysis.models import ArticlesImpact
from invenio_db import db


def get_authors_max_affiliation(author, country_list):
    max_aff = None
    max_value = 0
    for affiliation in author['affiliations']:
        if country_list[affiliation['country']] > max_value:
            max_value = country_list[affiliation['country']]
            max_aff = affiliation
    return max_aff


@shared_task
def calculate_articles_impact(from_date=None, until_date=None,
                              countries_ordering="value1", **kwargs):

    query = {
        '_source': ['authors', 'control_number'],
        'query': {
            'range': {
                'record_creation_date': {
                    "gte": from_date,
                    'lt': until_date,
                    'boost': 1
                }
            }
        }
    }
    search_results = es.search(index='records-record',
                               doc_type='record-v1.0.0',
                               body=query)

    countries_gdp = Gdp.query.all()
    country_list = {
        country.name: getattr(country, countries_ordering)
        for country in countries_gdp
    }

    for i, article in enumerate(search_results['hits']['hits']):
        details = {
            'countries_ordering': countries_ordering,
            'authors': []
        }
        result = {}
        for author in article['authors']:
            max_aff = get_authors_max_affiliation(author, country_list)
            details['authors']['raw_name'] = {
                'affiliation': max_aff['value'],
                'country': max_aff['country']
            }
            if max_aff['country'] in result:
                result[max_aff['country']] += 1
            else:
                result[max_aff['country']] = 1

        country_ai = ArticlesImpact.query.filter_by(
            control_number=article['control_number']).one_or_none()
        if country_ai:
            country_ai.details = details
            country_ai.result = result
        else:
            country_ai = ArticlesImpact(
                control_number=article['control_number'],
                details=details,
                result=result)

        db.session.add(country_ai)
    db.session.commit()

    # if signals:
    #     oaiharvest_finished.send(request, records=records, name=name, **kwargs)
