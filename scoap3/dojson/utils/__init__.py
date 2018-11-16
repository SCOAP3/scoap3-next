# -*- coding: utf-8 -*-
#
# This file is part of INSPIRE.
# Copyright (C) 2015, 2016 CERN.
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
# In applying this licence, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

"""DoJSON related utilities."""

from __future__ import absolute_import, division, print_function

import re
import six

try:
    from flask import current_app
except ImportError:  # pragma: no cover
    current_app = None

from scoap3.config import (
    ARXIV_TO_INSPIRE_CATEGORY_MAPPING,
    INSPIRE_RANK_TYPES,
)


def classify_field(value):
    """Classify value as a key of ARXIV_TO_INSPIRE_CATEGORY_MAPPING."""
    if not value:
        return None
    elif not isinstance(value, six.string_types):
        return None
    else:
        casted_value = value.upper()
        for name, category in six.iteritems(ARXIV_TO_INSPIRE_CATEGORY_MAPPING):
            if name.upper() == casted_value:
                return category
            elif category.upper() == casted_value:
                return category
        return 'Other'


def classify_rank(value):
    """Classify raw string as one of the keys in INSPIRE_RANK_TYPES."""
    if not value:
        return None
    elif not isinstance(value, six.string_types):
        return None
    else:
        casted_value = value.upper().replace('.', '')
        for rank_name, rank_mapping in INSPIRE_RANK_TYPES.items():
            if rank_name in casted_value:
                return rank_name
            else:
                if rank_mapping.get('alternative_names'):
                    for alternative in rank_mapping['alternative_names']:
                        if alternative in casted_value:
                            return rank_name
                if rank_mapping.get('abbreviations'):
                    for abbrev in rank_mapping['abbreviations']:
                        if abbrev == casted_value:
                            return rank_name

        return 'OTHER'


def create_profile_url(profile_id):
    """Create HEP author profile link based on the profile_id."""
    base_url = 'http://repo.scoap3.org/record/'

    try:
        int(profile_id)
        return base_url + str(profile_id)
    except (TypeError, ValueError):
        return ''


def get_int_value(d, k):
    """Get a value in a dict and cast it to int if possible."""
    try:
        return int(d.get(k))
    except (TypeError, ValueError):
        return None


def get_recid_from_ref(ref_obj):
    """Retrieve recid from jsonref reference object.

    If no recid can be parsed, return None.
    """
    if not isinstance(ref_obj, dict):
        return None
    url = ref_obj.get('$ref', '')
    try:
        res = int(url.split('/')[-1])
    except ValueError:
        res = None
    return res


def get_record_ref(recid, record_type='record'):
    """Create record jsonref reference object from recid.

    None recids will return a None object.
    Valid recids will return an object in the form of:
        {'$ref': url_for_record}
    """
    if recid is None:
        return None
    default_server = 'http://repo.scoap3.org'
    if current_app:
        server = current_app.config.get('SERVER_NAME') or default_server
    else:
        server = default_server
    # This config might also be http://inspirehep.net or
    # https://inspirehep.net.
    if not re.match('^https?://', server):
        server = 'http://{}'.format(server)
    return {'$ref': '{}/{}/{}'.format(server, record_type, recid)}


def legacy_export_as_marc(json, tabsize=4):
    """Create the MARCXML representation using the producer rules."""

    def encode_for_marcxml(value):
        from invenio_utils.text import encode_for_xml
        if isinstance(value, unicode):
            value = value.encode('utf8')
        return encode_for_xml(str(value), wash=True)

    export = ['<record>\n']

    for key, value in sorted(six.iteritems(json)):
        if not value:
            continue
        if key.startswith('00') and len(key) == 3:
            # Controlfield
            if isinstance(value, (tuple, list)):
                value = value[0]
            export += ['\t<controlfield tag="%s">%s'
                       '</controlfield>\n'.expandtabs(tabsize)
                       % (key, encode_for_marcxml(value))]
        else:
            tag = key[:3]
            try:
                ind1 = key[3].replace("_", "")
            except:  # noqa todo: implement proper exception handling (E722 do not use bare except)
                ind1 = ""
            try:
                ind2 = key[4].replace("_", "")
            except:  # noqa todo: implement proper exception handling (E722 do not use bare except)
                ind2 = ""
            if isinstance(value, dict):
                value = [value]
            for field in value:
                export += ['\t<datafield tag="%s" ind1="%s" '
                           'ind2="%s">\n'.expandtabs(tabsize)
                           % (tag, ind1, ind2)]
                if field:
                    for code, subfieldvalue in six.iteritems(field):
                        if subfieldvalue:
                            if isinstance(subfieldvalue, (list, tuple)):
                                for val in subfieldvalue:
                                    export += ['\t\t<subfield code="%s">%s'
                                               '</subfield>\n'.expandtabs(tabsize)
                                               % (code, encode_for_marcxml(val))]
                            else:
                                export += ['\t\t<subfield code="%s">%s'
                                           '</subfield>\n'.expandtabs(tabsize)
                                           % (code,
                                              encode_for_marcxml(subfieldvalue))]
                export += ['\t</datafield>\n'.expandtabs(tabsize)]
    export += ['</record>\n']
    return "".join(export)


def strip_empty_values(obj):
    """Recursively strips empty values."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            value = strip_empty_values(value)
            if value or value is False or value == 0:
                obj[key] = value
            else:
                del obj[key]
        return obj
    elif isinstance(obj, (list, tuple, set)):
        new_obj = [strip_empty_values(v) for v in obj]
        new_obj = [v for v in new_obj if v or v is False or v == 0]
        return type(obj)(new_obj)
    else:
        return obj
