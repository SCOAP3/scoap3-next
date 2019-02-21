import json
from os import path

from invenio_workflows import Workflow
from workflow.engine_db import WorkflowStatus

from scoap3.modules.records.util import create_from_json
from tests.responses import get_response_dir


def test_hindawi():
    file_path = path.join(get_response_dir(), 'hepcrawl', 'hindawi.json')
    with open(file_path, 'rt') as f:
        json_data = json.loads(f.read())

    workflow_id = create_from_json({'records': [json_data]}, apply_async=False)
    workflow = Workflow.query.get(workflow_id)

    assert workflow.status == WorkflowStatus.COMPLETED