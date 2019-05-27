import re

import requests_mock
from invenio_pidstore.models import PersistentIdentifier
from invenio_records import Record
from invenio_workflows import Workflow
from mock import patch
from workflow.errors import HaltProcessing

from scoap3.modules.records.util import create_from_json
from tests.responses import read_hep_schema, read_titles_schema, read_response_as_json


def mock_halt(msg, eng):
    raise HaltProcessing(msg)


def run_article_upload_with_file(input_json_filename, mock_address):
    """Uses input_json_filename to load hepcrawl response and to run article_upload workflow.
    Returns the Workflow object."""

    json_data = read_response_as_json('hepcrawl', input_json_filename)
    return run_article_upload_with_data(json_data, mock_address)


def run_article_upload_with_data(input_json_data, mock_address):
    """Runs article_upload workflow with input_json_data.
    Returns the Workflow object."""

    with patch('scoap3.modules.workflows.workflows.articles_upload.__halt_and_notify', mock_halt):
        mock_address.register_uri('GET', '/schemas/hep.json', content=read_hep_schema())
        mock_address.register_uri('GET', '/schemas/elements/titles.json', content=read_titles_schema())
        mock_address.register_uri(
            requests_mock.ANY,
            re.compile('.*(indexer).*'),
            real_http=True,
        )
        workflow_id = create_from_json({'records': [input_json_data]}, apply_async=False)[0]

    return Workflow.query.get(workflow_id)


def get_record_from_workflow(workflow):
    assert len(workflow.objects) == 1
    workflow_object = workflow.objects[0]

    recid = workflow_object.data['control_number']
    pid = PersistentIdentifier.get('recid', recid)

    return Record.get_record(pid.object_uuid)
