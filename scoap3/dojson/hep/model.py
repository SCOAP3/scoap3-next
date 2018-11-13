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

"""HEP model definition."""

from __future__ import absolute_import, division, print_function

from dojson.utils import force_list

from ..schema import SchemaOverdo
from ..utils import get_record_ref

from collections import MutableMapping, MutableSequence

from dojson import Overdo
from .compat import iteritems
from dojson.errors import IgnoreKey, MissingRule
from dojson.utils import GroupableOrderedDict


class Underdo(Overdo):
    """Translation index specification for reverse marc21 translation."""

    def do(self, blob, ignore_missing=True, exception_handlers=None):
        """Translate blob values and instantiate new model instance.
        Takes out the indicators, if any, from the returned dictionary and puts
        them into the key.
        :param blob: ``dict``-like object on which the matching rules are
                     going to be applied.
        :param ignore_missing: Set to ``False`` if you prefer to raise
                               an exception ``MissingRule`` for the first
                               key that it is not matching any rule.
        :param exception_handlers: Give custom exception handlers to take care
                                   of non-standard names that are installation
                                   specific.
        .. versionadded:: 1.0.0
           ``ignore_missing`` allows to specify if the function should raise
           an exception.
        .. versionadded:: 1.1.0
           ``exception_handlers`` allows unknown keys to treated in a custom
           fashion.
        """
        handlers = {IgnoreKey: None}
        handlers.update(exception_handlers or {})

        if ignore_missing:
            handlers.setdefault(MissingRule, None)

        output = []

        if self.index is None:
            self.build()

        if '__order__' in blob and not isinstance(blob, GroupableOrderedDict):
            blob = GroupableOrderedDict(blob)

        if '__order__' in blob:
            items = blob.iteritems(repeated=True)
        else:
            items = iteritems(blob)

        for key, values in items:
            if type(values) != list:
                values = [values]
            for value in values:
                try:
                    result = self.index.query(key)
                    if not result:
                        raise MissingRule(key)

                    name, creator = result
                    item = creator(output, key, value)
                    if isinstance(item, MutableMapping):
                        field = '{0}{1}{2}'.format(
                            name, item.pop('$ind1', '_'),
                            item.pop('$ind2', '_'))
                        if '__order__' in item:
                            item = GroupableOrderedDict(item)
                        output.append((field, item))
                    elif isinstance(item, MutableSequence):
                        for v in item:
                            try:
                                field = '{0}{1}{2}'.format(
                                    name, v.pop('$ind1', '_'),
                                    v.pop('$ind2', '_'))
                            except AttributeError:
                                field = name
                            output.append((field, v))
                    else:
                        output.append((name, item))
                except Exception as exc:
                    if exc.__class__ in handlers:
                        handler = handlers[exc.__class__]
                        if handler is not None:
                            handler(exc, output, key, value)
                    else:
                        raise

        return GroupableOrderedDict(output)


def add_book_info(record, blob):
    """Add link to the appropriate book record."""
    collections = []
    if 'collections' in record:
        for c in record.get('collections', ''):
            if c.get('primary', ''):
                collections.append(c.get('primary').lower())
        if 'bookchapter' in collections:
            pubinfos = force_list(blob.get("773__", []))
            for pubinfo in pubinfos:
                if pubinfo.get('0'):
                    record['book'] = {
                        'record': get_record_ref(
                            int(force_list(pubinfo.get('0'))[0]), 'literature')
                    }


class Publication(SchemaOverdo):

    def do(self, blob, **kwargs):
        output = super(Publication, self).do(blob, **kwargs)
        add_book_info(output, blob)
        return output


hep = Overdo(entry_point_group="scoap3.dojson.hep")
hep2marc = Underdo(entry_point_group="scoap3.dojson.hep2marc")
