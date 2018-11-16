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

from scoap3.utils.dedupers import dedupe_list

from ..model import hep, hep2marc
from ...utils import create_profile_url, get_record_ref
from ...utils.nations import find_country


@hep.over('authors', '^[17]00[103_].')
def authors(self, key, value):
    """Main Entry-Personal Name."""
    value = utils.force_list(value)

    def get_value(value):
        affiliations = []
        if value.get('v'):
            affiliations = dedupe_list(utils.force_list(value.get('v')))

            tmp_affiliations = []
            for aff in affiliations:
                country = find_country(aff)
                tmp_affiliations.append({'value': aff, 'country': country})
            affiliations = tmp_affiliations

        person_recid = None
        if value.get('x'):
            try:
                person_recid = int(value.get('x'))
            except:  # noqa todo: implement proper exception handling (E722 do not use bare except)
                pass
        inspire_id = ''
        if value.get('i'):
            inspire_id = utils.force_list(value.get('i'))[0]
        person_record = get_record_ref(person_recid, 'authors')
        ret = {
            'full_name': value.get('a'),
            # 'role': value.get('e'),
            # 'alternative_name': value.get('q'),
            # 'inspire_bai': value.get('w'),
            # 'orcid': value.get('j'),
            # 'record': person_record,
            # 'email': value.get('m'),
            # 'affiliations': affiliations,
            'profile': {"__url__": create_profile_url(value.get('x'))},
            'curated_relation': value.get('y', 0) == 1
        }
        if inspire_id:
            ret['inspire_id'] = inspire_id
        if value.get('m'):
            ret['email'] = value.get('m')
        if value.get('e'):
            ret['role'] = value.get('e')
        if value.get('j'):
            ret['orcid'] = value.get('j')
        if value.get('q'):
            ret['alternative_name'] = value.get('q')
        if person_record:
            ret['person_record'] = person_record
        if affiliations:
            ret['affiliations'] = affiliations
        # HACK: This is to workaround broken records where multiple authors
        # got meshed up together.
        if isinstance(ret['full_name'], (list, tuple)):
            import warnings
            warnings.warn("Record with mashed-up author list! Taking first author: {}".format(value))
            ret['full_name'] = ret['full_name'][0]
        return ret

    authors = self.get('authors', [])

    if key.startswith('100'):
        authors.insert(0, get_value(value[0]))
    else:
        for single_value in value:
            authors.append(get_value(single_value))

    # XXX: duplicates are not stripped here, because this is an expensive
    #      operation that would be repeated one time per field.
    return authors


@hep2marc.over('100', '^authors$')
@utils.filter_values
def authors2marc(self, key, value):
    """Main Entry-Personal Name."""
    field_map = {
        'fullname': 'a',
        'affiliation': 'u',
        'orcid': 'j'
    }
    order = utils.map_order(field_map, value)

    affiliations = []
    for aff in value.get('affiliations', []):
        affiliations.append(aff['value'])

    return {
        '__order__': tuple(order) if len(order) else None,
        'a': value.get('full_name'),
        'j': value.get('orcid'),
        'u': affiliations
    }


@hep.over('corporate_author', '^110[10_2].')
@utils.for_each_value
def corporate_author(self, key, value):
    """Main Entry-Corporate Name."""
    return value.get('a')


@hep2marc.over('110', '^corporate_author$')
@utils.for_each_value
def corporate_author2marc(self, key, value):
    """Main Entry-Corporate Name."""
    return {
        'a': value,
    }
