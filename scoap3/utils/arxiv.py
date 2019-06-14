# -*- coding: utf-8 -*-
#
# This file is part of INSPIRE.
# Copyright (C) 2014, 2015, 2016 CERN.
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

"""Helpers for arXiv.org."""

from __future__ import absolute_import, division, print_function

import logging

from inspire_utils.record import get_value
from lxml import etree

from scoap3.utils.http import requests_retry_session

logger = logging.getLogger(__name__)

url = 'http://export.arxiv.org/api/query?search_query={0}'
xml_namespaces = {'arxiv': 'http://arxiv.org/schemas/atom',
                  'w3': 'http://www.w3.org/2005/Atom'}


def get_clean_arXiv_id(record):
    """Return the arXiv identifier from given record."""
    return clean_arxiv(get_value(record, 'arxiv_eprints.value[0]'))


def clean_arxiv(arxiv):
    # drop 'arxiv:' prefix, version and other information if there is
    # also force ascii encoding and strip unnecessary characters
    if arxiv is None:
        return None

    return arxiv.split(':')[-1].split('v')[0].split(' ')[0].encode('ascii').strip('"\'')


def get_arxiv_categories_from_response_xml(xml):
    entry_count = len(xml.xpath('//w3:entry', namespaces=xml_namespaces))

    # make sure we have exactly one result in the xml
    if entry_count != 1:
        return []

    primary_category = xml.xpath('//arxiv:primary_category/@term', namespaces=xml_namespaces)

    if not primary_category:
        return []

    if len(primary_category) > 1:
        logger.error('Arxiv returned %d primary category.' % len(primary_category))
        return []

    secondary_categories = xml.xpath('//w3:category/@term', namespaces=xml_namespaces)

    # remove primary category from secondary category list, if exists
    try:
        secondary_categories.remove(primary_category[0])
    except ValueError:
        # primary category is not listed as secondary category
        pass

    return primary_category + secondary_categories


def get_arxiv_categories(arxiv_id=None, title=None, doi=None):
    """
    Return a list of arxiv categories based on the specified arXiv identifier and/or title and/or doi.

    The identifier and title (if given) are both forwarded to the arXiv api.

    First element of the returned list is the primary category.
    In case categories cannot be found, empty list is returned.
    """

    if arxiv_id is None and title is None and doi is None:
        raise ValueError('One of the arxiv_id, title and doi parameters has to be different then None.')

    # make sure we have a clean arxiv number
    arxiv_id = clean_arxiv(arxiv_id)

    query = []
    if arxiv_id:
        query.append('id:%s' % arxiv_id)

    if title:
        title = title.replace('-', '?').encode('ascii', 'replace')
        query.append('ti:"%s"' % title)

    if doi:
        query.append('doi:"%s"' % doi)

    request_url = url.format(' '.join(query))
    data = requests_retry_session().get(request_url)

    categories = []
    if data.status_code == 200:
        xml = etree.fromstring(data.content)
        categories = get_arxiv_categories_from_response_xml(xml)
        if not categories:
            logger.warning('Could not get arxiv categories for id="%s" title="%s" doi="%s"' % (arxiv_id, title, doi))
    else:
        logger.error('Got status_code %s from arXiv when looking for categires for id="%s" title="%s" doi="%s"' % (
            data.status_code, arxiv_id, title, doi))

    return categories
