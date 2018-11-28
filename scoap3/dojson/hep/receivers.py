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

"""Contains signal receivers for HEP dojson processing."""

from invenio_records.signals import before_record_insert, before_record_update


@before_record_insert.connect
@before_record_update.connect
def remove_duplicate_authors(sender, *args, **kwargs):
    """Remove duplicate authors.

    Has to be done here rather than when importing the record
    for performance reasons."""
    pass
    # try:
    #     record['authors'] = dedupe_list_of_dicts(record['authors'])
    # except KeyError:
    #     pass
