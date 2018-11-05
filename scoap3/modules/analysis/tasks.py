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

import re
import urllib
import xml.etree.ElementTree as ET

from celery import shared_task
from invenio_db import db
from invenio_search.api import current_search_client as es
from scoap3.dojson.utils.nations import find_nation
from scoap3.modules.analysis.models import ArticlesImpact, Gdp
from sqlalchemy.orm.attributes import flag_modified

inspire_namespace = {'a': 'http://www.loc.gov/MARC21/slim'}
es_result_mock = {
    'hits': {
        'hits': [],
        'total': 0
    }
}
inspire_base_url = "http://inspirehep.net/search?of=xm&sf=earliestdate&so=d&rm=&sc=0&ot=001,024,100,700,260,773"


def get_query(start_index, step, from_date, until_date):
    return {
        '_source': ['authors', 'control_number', 'dois', 'earliest_date', 'publication_info', 'record_creation_date'],
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
    for affiliation in author.get('affiliations', []):
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


def fetch_url(jrec, size, query):
    final_url = '&'.join([inspire_base_url, urllib.urlencode({'jrec': jrec,
                                                              'rg': size,
                                                              'p': query})])
    req = urllib.urlopen(final_url)
    req_text = req.read().replace(b'\n', b'')
    root = ET.fromstring(req_text)
    total_records_count = re.findall('(?<=Search-Engine-Total-Number-Of-Results: )\d{1,10}', req_text)
    if total_records_count:
        total_records_count = total_records_count[0]
    else:
        total_records_count = 0
    return total_records_count, root.findall('./a:record', inspire_namespace)


def parse_inspire_records(size, query, jrec=1):
    articles = es_result_mock
    jrec = jrec
    articles['hits']['total'], records = fetch_url(jrec, size, query)

    for r in records:
        json_record = {'_source': {'authors': [], 'publication_info': []}}
        authors = r.findall('./a:datafield[@tag="100"]', inspire_namespace)
        authors.extend(r.findall('./a:datafield[@tag="700"]',
                       inspire_namespace))
        for author in authors:
            json_author = {
                'full_name': author.find('./a:subfield[@code="a"]',
                                         inspire_namespace).text.encode('utf-8'),
                'affiliations': []
            }
            affs = author.findall('./a:subfield[@code="v"]',
                                  inspire_namespace)
            for aff in affs:
                json_aff = {
                    'value': aff.text.encode('utf-8'),
                    'country': find_nation(aff.text.encode('utf-8'))
                }
                json_author['affiliations'].append(json_aff)
            json_record['_source']['authors'].append(json_author)
        json_record['_source']['control_number'] = int(r.find('./a:controlfield[@tag="001"]', inspire_namespace).text)
        json_record['_source']['dois'] = [{'value': r.find('./a:datafield[@tag="024"][@ind1="7"]/a:subfield[@code="a"]', inspire_namespace).text}]
        json_record['_source']['record_creation_date'] = r.find('./a:datafield[@tag="260"]/a:subfield[@code="c"]', inspire_namespace).text
        json_record['_source']['earliest_date'] = json_record['_source']['record_creation_date']
        json_record['_source']['publication_info'].append({'journal_title': r.find('./a:datafield[@tag="773"]/a:subfield[@code="p"]', inspire_namespace).text + r.find('./a:datafield[@tag="773"]/a:subfield[@code="v"]', inspire_namespace).text})
        articles['hits']['hits'].append(json_record)
    return articles


@shared_task
def calculate_articles_impact(from_date=None, until_date=None,
                              countries_ordering="value1", step=10,
                              inspire_query=None, **kwargs):
    count = 0
    jrec = 1
    country_list = get_country_list(countries_ordering)

    if inspire_query:
        print("Calculating articles impact for Inspire query: {}".format(
              inspire_query))
    else:
        print("Calculating articles impact between: {} and {}".format(
              from_date, until_date))

    while True:
        if inspire_query:
            search_results = parse_inspire_records(100, inspire_query, jrec)
        else:
            search_results = es.search(index='records-record',
                                   doc_type='record-v1.0.0',
                                   body=get_query(count, step, from_date, until_date))

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
            country_ai.creation_date = article['_source'].get('record_creation_date', article['_source']['earliest_date'])
            country_ai.journal = article['_source']['publication_info'][0]['journal_title']
            country_ai.details = details
            country_ai.results = result
            flag_modified(country_ai, 'details')
            flag_modified(country_ai, 'results')

            db.session.add(country_ai)
        db.session.commit()

        count += len(search_results['hits']['hits'])
        jrec += step
        if count < int(search_results['hits']['total']):
            print("Count {} is < than {}. Running next query: {}".format(
                count,
                search_results['hits']['total'],
                get_query(count, step, from_date, until_date))
            )
        else:
            print("Finished article impact calculation.")
            break
