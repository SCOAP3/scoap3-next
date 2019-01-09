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
import urllib
from xml.dom.minidom import parseString

url = 'http://export.arxiv.org/api/query?search_query=id:{0}'


def get_clean_arXiv_id(record):
    """Return the arXiv identifier from given record."""
    arxiv_id = record.get("arxiv_id")
    if not arxiv_id:
        arxiv_eprints = record.get('arxiv_eprints', [])
        for element in arxiv_eprints:
            if element.get("value", ""):
                arxiv_id = element.get("value", "")

    if arxiv_id:
        return arxiv_id.split(':')[-1]
    else:
        return None


def get_arxiv_categories(arxiv_id):
    try:
        data = urllib.urlopen(url.format(arxiv_id)).read()
    except Exception as e:
        raise e
        # data = None
    categories = []
    if data:
        xml = parseString(data)
        for tag in xml.getElementsByTagName('category'):
            try:
                categories.append(tag.attributes['term'].value)
            except KeyError:
                pass
    if not categories:
        raise Exception(data)
    return categories


def get_arxiv_primary_category(arxiv_id):
    # arxiv ids can have version at the end, cut that.
    arxiv_id = arxiv_id.split('v')[0]

    data = urllib.urlopen(url.format(arxiv_id)).read()

    if data:
        xml = parseString(data)
        category = xml.getElementsByTagName('arxiv:primary_category')
        if not category or len(category) > 1:
            raise AttributeError('Exactly one primary category must be present.')
        return category[0].attributes['term'].value

    return None
