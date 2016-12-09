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
from datetime import datetime

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

def record_not_published_before_2014(obj, eng):
    """Make sure record was published in 2014 and onwards."""
    datetime_object = datetime.strptime(obj.data['imprints'][0]['date'], '%Y-%m-%d')
    if not datetime_object.year >= 2014:
        eng.halt("Record published before 2014")
    return True


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
        IF(
            record_not_published_before_2014,
            [
                # IF(
                #   is_record_from_partial_journal,
                #   check_arxiv_number
                #   )
                # add_collections,
                # add_nations,
                # check_compliance_24h
                # check_compliance_files_not_corupted
                # check_compliance_pdfa_validation
                # check_compliance_funded_by_scoap3
                # check_compliance_copyrights
                # check_complaince_available_at_publishers_website
                # store_record
            ]
        )
    ]
