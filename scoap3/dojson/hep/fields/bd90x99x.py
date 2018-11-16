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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with INSPIRE. If not, see <http://www.gnu.org/licenses/>.
#
# In applying this licence, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

"""MARC 21 model definition."""

from __future__ import absolute_import, division, print_function

from dojson import utils

from ..model import hep, hep2marc
from ...utils import get_recid_from_ref, get_record_ref, get_int_value
from .processors import ReferenceBuilder
from functools import partial
from scoap3.utils.helpers import force_force_list


@hep.over('references', '^999C5')
def references(self, key, value):
    """Produce list of references."""
    value = force_force_list(value)

    def get_value(value):
        # Retrieve fields as described here:
        # https://twiki.cern.ch/twiki/bin/view/Inspire/DevelopmentRecordMarkup.
        rb = ReferenceBuilder()
        mapping = [
            ('o', rb.set_number),
            ('m', rb.add_misc),
            ('x', partial(rb.add_raw_reference, source='dojson')),
            ('1', rb.set_texkey),
            ('u', rb.add_url),
            ('r', rb.add_report_number),
            ('s', rb.set_pubnote),
            ('p', rb.set_publisher),
            ('y', rb.set_year),
            ('i', rb.add_uid),
            ('b', rb.add_uid),
            ('a', rb.add_uid),
            ('c', rb.add_collaboration),
            ('q', rb.add_title),
            ('t', rb.add_title),
            ('h', rb.add_refextract_authors_str),
            ('e', partial(rb.add_author, role='ed.'))
        ]

        for field, method in mapping:
            for element in force_force_list(value.get(field)):
                if element:
                    method(element)

        if '0' in value:
            recid = get_int_value(value, '0')
            rb.set_record(get_record_ref(recid, 'literature'))

        return rb.obj

    references = self.get('references', [])
    references.extend(get_value(v) for v in value)
    return references


@hep2marc.over('999C5', 'references')
@utils.for_each_value
@utils.filter_values
def references2marc(self, key, value):
    """Produce list of references."""
    return {
        '0': get_recid_from_ref(value.get('record')),
        '1': value.get('texkey'),
        'a': value.get('doi'),
        'c': value.get('collaboration'),
        'e': value.get('editors'),
        'h': value.get('authors'),
        'm': value.get('misc'),
        'o': value.get('number'),
        'i': value.get('isbn'),
        'p': value.get('publisher'),
        'q': value.get('maintitle'),
        'r': value.get('report_number'),
        't': value.get('title'),
        'u': value.get('urls'),
        's': value.get('journal_pubnote'),
        'x': value.get('raw_reference'),
        'y': value.get('year'),
    }


@hep.over('refextract', '^999C6')
@utils.for_each_value
@utils.filter_values
def refextract(self, key, value):
    """Contains info from refextract."""
    return {
        'comment': value.get('c'),
        'time': value.get('t'),
        'version': utils.force_list(value.get('v')),
        'source': value.get('s'),
    }


@hep2marc.over('999C6', 'refextract')
@utils.for_each_value
@utils.filter_values
def refextract2marc(self, key, value):
    """Contains info from refextract."""
    return {
        'c': value.get('comment'),
        't': value.get('time'),
        'v': value.get('version'),
        's': value.get('source'),
    }


@hep.over('collections', '^980..')
@utils.for_each_value
@utils.filter_values
def collections(record, key, value):
    """Parse custom MARC tag 980."""
    special = None
    deleted = None
    if value.get('c') in ['EDITORIAL', 'ERRATUM', 'ADDENDUM', 'CORRIGENDUM', 'LETTER_TO_THE_EDITOR']:
        special = value.get('c')
    else:
        deleted = value.get('c')
    return {
        'primary': value.get('a'),
        'secondary': value.get('b'),
        'special': special,
        'deleted': deleted,
    }


# TODO - this needs to be updated to convert back 'special' collections to MARC
@hep2marc.over('980', '^collections$')
@utils.reverse_for_each_value
@utils.filter_values
def reverse_collections(self, key, value):
    """Reverse colections field to custom MARC tag 980."""
    return {
        'a': value.get('primary'),
        'b': value.get('secondary'),
        'c': value.get('deleted'),
    }
