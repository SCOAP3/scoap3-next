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

from scoap3.utils.dedupers import dedupe_list_of_dicts

from ..hep.model import hep
from ..utils import (
    classify_field,
    get_recid_from_ref,
    get_record_ref,
    strip_empty_values,
)


def self_url(index):
    def _self_url(self, key, value):
        """Url of the record itself."""
        self['control_number'] = value
        return get_record_ref(value, index)

    return _self_url


hep.over('self', '^001')(self_url('record'))


@hep.over('agency_code', '^003')
def agency_code(self, key, value):
    """Control Number Identifier."""
    return value


@hep.over('date_and_time_of_latest_transaction', '^005')
def date_and_time_of_latest_transaction(self, key, value):
    """Date and Time of Latest Transaction."""
    return value


@hep.over('oai_pmh', '^909CO')
@utils.for_each_value
@utils.filter_values
def oai_pmh(self, key, value):
    """Local OAI-PMH record information."""
    return {
        'id': value.get('o'),
        'set': value.get('p'),
        'previous_set': value.get('q'),
    }


@utils.for_each_value
@utils.filter_values
def oai_pmh2marc(self, key, value):
    """Local OAI-PMH record information."""
    return {
        'o': value.get('id'),
        'p': value.get('set'),
        'q': value.get('previous_set')
    }


@hep.over('creation_modification_date', '^961..')
@utils.for_each_value
@utils.filter_values
def creation_modification_date(self, key, value):
    """Original creation and modification date."""
    return {
        'modification_date': value.get('c'),
        'creation_date': value.get('x'),
    }


@utils.for_each_value
@utils.filter_values
def creation_modification_date2marc(self, key, value):
    """Original creation and modification date."""
    return {
        'c': value.get('modification_date'),
        'x': value.get('creation_date')
    }


@hep.over('spires_sysnos', '^970..')
@utils.ignore_value
def spires_sysnos(self, key, value):
    """Old SPIRES number and new_recid from 970."""
    value = utils.force_list(value)
    sysnos = []
    new_recid = None
    for val in value:
        if 'a' in val:
            # Only append if there is something
            sysnos.append(val.get('a'))
        elif 'd' in val:
            new_recid = val.get('d')
    if new_recid is not None:
        # FIXME we are currently using the default /record API. Which might
        # resolve to a 404 response.
        self['new_record'] = get_record_ref(new_recid)
    return sysnos or None


@hep.over('collections', '^980..')
def collections(self, key, value):
    """Collection this record belongs to."""
    value = utils.force_list(value)

    def get_value(value):
        primary = ''
        if isinstance(value.get('a'), list):
            primary = value.get('a')[0]
        else:
            primary = value.get('a')
        return {
            'primary': primary,
            'secondary': value.get('b'),
            'deleted': value.get('c'),
        }

    collections = self.get('collections', [])

    for val in value:
        collections.append(get_value(val))

    contains_list = False
    for element in collections:
        for k, v in enumerate(element):
            if isinstance(element[v], list):
                contains_list = True
                break
    if contains_list:
        return strip_empty_values(collections)
    else:
        return dedupe_list_of_dicts(collections)


@utils.for_each_value
@utils.filter_values
def collections2marc(self, key, value):
    """Collection this record belongs to."""
    return {
        'a': value.get('primary'),
        'b': value.get('secondary'),
        'c': value.get('deleted')
    }


@hep.over('deleted_records', '^981..')
@utils.for_each_value
@utils.ignore_value
def deleted_records(self, key, value):
    """Recid of deleted record this record is master for."""
    # FIXME we are currently using the default /record API. Which might
    # resolve to a 404 response.
    return get_record_ref(value.get('a'))


@hep.over('fft', '^FFT..')
@utils.for_each_value
@utils.filter_values
def fft(self, key, value):
    """Collection this record belongs to."""
    return {
        'url': value.get('a'),
        'docfile_type': value.get('t'),
        'flag': value.get('o'),
        'description': value.get('d'),
        'filename': value.get('n'),
    }


@hep.over('FFT', 'fft')
@utils.for_each_value
@utils.filter_values
def fft2marc(self, key, value):
    """Collection this record belongs to."""
    return {
        'a': value.get('url'),
        't': value.get('docfile_type'),
        'o': value.get('flag'),
        'd': value.get('description'),
        'n': value.get('filename'),
    }


@utils.for_each_value
@utils.filter_values
def deleted_records2marc(self, key, value):
    """Deleted recids."""
    return {
        'a': get_recid_from_ref(value)
    }


@hep.over('field_categories', '^650[1_][_7]')
@utils.for_each_value
def field_categories(self, key, value):
    """Field categories."""
    self.setdefault('field_categories', [])

    _terms = utils.force_list(value.get('a'))

    if _terms:
        for _term in _terms:
            term = classify_field(_term)

            scheme = 'INSPIRE' if term else None

            _scheme = value.get('2')
            if isinstance(_scheme, (list, tuple)):
                _scheme = _scheme[0]

            source = value.get('9')
            if source:
                if 'automatically' in source:
                    source = 'INSPIRE'

            self['field_categories'].append({
                'source': source,
                '_scheme': _scheme,
                'scheme': scheme,
                '_term': _term,
                'term': term,
            })

        self['field_categories'] = dedupe_list_of_dicts(
            self['field_categories'])


@hep.over('urls', '^856.[10_28]')
@utils.for_each_value
def urls(self, key, value):
    """URL to external resource."""
    self.setdefault('urls', [])

    description = value.get('y')
    if isinstance(description, (list, tuple)):
        description = description[0]

    _urls = utils.force_list(value.get('u'))

    if _urls:
        for _url in _urls:
            self['urls'].append({
                'description': description,
                'value': _url,
            })

        self['urls'] = dedupe_list_of_dicts(self['urls'])
