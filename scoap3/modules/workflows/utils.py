# -*- coding: utf-8 -*-
#
# This file is part of SCOAP3.
# Copyright (C) 2018 CERN.
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
from invenio_db import db
from invenio_search import current_search_client
from invenio_workflows import start, Workflow
from workflow.engine_db import WorkflowStatus


def start_compliance_workflow(record):
    """
    Starts a compliance workflow for the given record.
    :param record: RecordMetadata object
    """
    start.apply_async(
        kwargs=dict(
            workflow_name='run_compliance',
            data=record.json
        )
    )


def delete_halted_workflows_for_doi(doi):
    """
    Deletes all workflow that contain the given doi and are in HALTED state.

    The workflow index will only be updated, when a WorkflowObjectModel instance is saved. When a workflow is halted,
    the connected object's status won't be changed, hence the index won't be updated. Because of all this, we cannot
    filter for HALTED state in ElasticSearch.
    """

    current_search_client.indices.refresh("scoap3-workflows-harvesting")
    search_result = current_search_client.search('scoap3-workflows-harvesting', q='metadata.dois.value:"%s"' % doi)

    workflow_ids = {x['_source']['_workflow']['id_workflow'] for x in search_result['hits']['hits']}
    for wid in workflow_ids:
        if wid:
            w = Workflow.query.get(wid)
            if w.status == WorkflowStatus.HALTED:
                db.session.delete(w)

    db.session.commit()
