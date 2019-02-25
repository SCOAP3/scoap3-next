import json
from os import path

from invenio_workflows import Workflow
from workflow.engine_db import WorkflowStatus

from scoap3.modules.records.util import create_from_json
from tests.responses import get_response_dir


def run_workflow(input_json_filename):
    """Use input_json_filename to load hepcrawl response and to run article_upload workflow."""

    file_path = path.join(get_response_dir(), 'hepcrawl', input_json_filename)
    with open(file_path, 'rt') as f:
        json_data = json.loads(f.read())

    workflow_id = create_from_json({'records': [json_data]}, apply_async=False)[0]
    return Workflow.query.get(workflow_id)


def test_hindawi():
    workflow = run_workflow('hindawi.json')
    assert workflow.status == WorkflowStatus.COMPLETED


def test_aps():
    workflow = run_workflow('aps.json')
    assert workflow.status == WorkflowStatus.COMPLETED


def test_elsevier():
    workflow = run_workflow('elsevier/elsevier.json')
    assert workflow.status == WorkflowStatus.COMPLETED


def test_springer():
    workflow = run_workflow('springer/springer.json')
    assert workflow.status == WorkflowStatus.COMPLETED


def test_oup():
    workflow = run_workflow('oup/oup.json')
    assert workflow.status == WorkflowStatus.COMPLETED
