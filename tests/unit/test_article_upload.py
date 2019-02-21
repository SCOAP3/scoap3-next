import json
from os import path

from invenio_workflows import Workflow
from workflow.engine_db import WorkflowStatus

from scoap3.modules.records.util import create_from_json
from tests.responses import get_response_dir


def common(input_json_filename):
    """Use input_json_filename to load hepcrawl response and to run article_upload workflow."""

    file_path = path.join(get_response_dir(), 'hepcrawl', input_json_filename)
    with open(file_path, 'rt') as f:
        json_data = json.loads(f.read())

    workflow_id = create_from_json({'records': [json_data]}, apply_async=False)
    workflow = Workflow.query.get(workflow_id)

    assert workflow.status == WorkflowStatus.COMPLETED


def test_hindawi():
    common('hindawi.json')


def test_aps():
    common('aps.json')
