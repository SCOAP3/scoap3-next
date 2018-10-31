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
from invenio_db import db
from invenio_search.api import current_search_client as es
from scoap3.modules.analysis.models import ArticlesImpact, Gdp
from sqlalchemy.orm.attributes import flag_modified


def get_query(start_index, step, from_date, until_date):
    return {
        '_source': ['authors', 'control_number', 'dois'],
        'from': start_index,
        'size': step,
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


def get_authors_max_affiliation(author, country_list):
    max_aff = None
    max_value = 0
    for affiliation in author['affiliations']:
        if country_list.get(affiliation['country'], 0) >= max_value:
            max_value = country_list.get(affiliation['country'], 0)
            max_aff = affiliation
    return max_aff


def get_country_list(countries_ordering):
    countries_gdp = Gdp.query.all()
    return {
        country.name.strip(): getattr(country, countries_ordering)
        for country in countries_gdp
    }


@shared_task
def calculate_articles_impact(from_date=None, until_date=None,
                              countries_ordering="value1", step=1, **kwargs):
    count = 0

    print("Calculating articles impact between: {} and {}".format(
        from_date, until_date))

    while True:
        search_results = es.search(index='records-record',
                                   doc_type='record-v1.0.0',
                                   body=get_query(count, step, from_date, until_date))

        country_list = get_country_list(countries_ordering)
        for article in search_results['hits']['hits']:
            details = {
                'countries_ordering': countries_ordering,
                'authors': {}
            }
            result = {}
            for author in article['_source'].get('authors', []):
                max_aff = get_authors_max_affiliation(author, country_list)
                if max_aff:
                    details['authors'][author['full_name']] = {
                        'affiliation': max_aff['value'],
                        'country': max_aff['country']
                    }
                    if max_aff['country'] in result:
                        result[max_aff['country']] += 1
                    else:
                        result[max_aff['country']] = 1
                else:
                    continue

            country_ai = ArticlesImpact.get_or_create(
                article['_source']['control_number'])
            country_ai.doi = article['_source']['dois'][0]['value']
            country_ai.details = details
            country_ai.results = result
            flag_modified(country_ai, 'details')
            flag_modified(country_ai, 'results')

            db.session.add(country_ai)
        db.session.commit()

        count += len(search_results['hits']['hits'])
        if count < search_results['hits']['total']:
            print("Count {} is < than {}. Running next query: {}".format(
                count,
                search_results['hits']['total'],
                get_query(count, step, from_date, until_date))
            )
        else:
            print("Finished article impact calculation.")
            break
