# -*- coding: utf-8 -*-
#
# This file is part of SCOAP3.
# Copyright (C) 2016 CERN.
#
# SCOAP3 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SCOAP3 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SCOAP3. If not, see <http://www.gnu.org/licenses/>.
#
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

"""Workflow for processing single Hindawi records harvested."""

from __future__ import absolute_import, division, print_function
from flask import url_for

from workflow.patterns.controlflow import (
    IF,
    IF_ELSE,
    IF_NOT,
)

def set_schema(obj, eng):
    """Make sure schema is set properly and resolve it."""
    if '$schema' not in obj.data:
        obj.data['$schema'] = "{data_type}.json".format(
            data_type=obj.data_type or eng.workflow_definition.data_type
        )

    if not obj.data['$schema'].startswith('http'):
        obj.data['$schema'] = url_for(
            'invenio_jsonschemas.get_schema',
            schema_path="records/{0}".format(obj.data['$schema'])
        )


def emit_record_signals(obj, eng):
    """Emit record signals to update record metadata."""
    from scoap3_records.signals import before_record_insert

    before_record_insert.send(obj.data)


class Hindawi(object):
    """Article ingestion workflow for Records collection."""
    name = "HEP"
    data_type = "harvesting"

    workflow = [
        # Make sure schema is set for proper indexing in Holding Pen
        set_schema,
        # Query locally or via legacy search API to see if article
        # is already ingested and this is an update
        # arxiv_fulltext_download,
        # arxiv_plot_extract,
        # arxiv_refextract,
        # arxiv_author_list("authorlist2marcxml.xsl"),
        # extract_journal_info,
        # IF(is_experimental_paper, [
        #     guess_experiments,
        # ]),
        # store_record
    ]
