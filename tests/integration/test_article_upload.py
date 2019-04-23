import json
import re
from os import path

import requests_mock
from invenio_pidstore.models import PersistentIdentifier
from invenio_records import Record
from invenio_workflows import Workflow
from mock import patch
from workflow.engine_db import WorkflowStatus
from workflow.errors import HaltProcessing

from scoap3.modules.records.util import create_from_json
from tests.responses import get_response_dir, read_hep_schema, read_titles_schema, read_response


def _get_record_from_workflow(workflow):
    assert len(workflow.objects) == 1
    workflow_object = workflow.objects[0]

    recid = workflow_object.data['control_number']
    pid = PersistentIdentifier.get('recid', recid)

    return Record.get_record(pid.object_uuid)


def mock_halt(msg, obj, eng):
    raise HaltProcessing(msg)


def run_workflow(input_json_filename, mock_address):
    """Use input_json_filename to load hepcrawl response and to run article_upload workflow."""

    file_path = path.join(get_response_dir(), 'hepcrawl', input_json_filename)
    with open(file_path, 'rt') as f:
        json_data = json.loads(f.read())

    with patch('scoap3.modules.workflows.workflows.articles_upload.__halt_and_notify', mock_halt):
        mock_address.register_uri('GET', '/schemas/hep.json', content=read_hep_schema())
        mock_address.register_uri('GET', '/schemas/elements/titles.json', content=read_titles_schema())
        mock_address.register_uri(
            requests_mock.ANY,
            re.compile('.*(indexer).*'),
            real_http=True,
        )
        workflow_id = create_from_json({'records': [json_data]}, apply_async=False)[0]

    return Workflow.query.get(workflow_id)


def test_hindawi():
    workflows_count = Workflow.query.count()

    with requests_mock.Mocker() as m:
        m.get('http://downloads.hindawi.com/journals/ahep/2019/4123108.pdf',
              content=read_response('article_upload', 'hindawi.com_journals_ahep_2019_4123108.pdf'))
        m.get('http://downloads.hindawi.com/journals/ahep/2019/4123108.xml',
              content=read_response('article_upload', 'hindawi.com_journals_ahep_2019_4123108.xml'))
        m.get('https://api.crossref.org/works/10.1155/2019/4123108',
              content=read_response('article_upload', 'crossref.org_works_10.1155_2019_4123108'))
        workflow = run_workflow('hindawi.json', m)

    assert workflow.status == WorkflowStatus.COMPLETED
    assert Workflow.query.count() - workflows_count == 1

    record = _get_record_from_workflow(workflow)
    assert len(record['_files']) == 2


def test_aps():
    workflows_count = Workflow.query.count()

    with requests_mock.Mocker() as m:
        m.get('http://export.arxiv.org/api/query?search_query=id:1811.06024',
              content=read_response('article_upload', 'export.arxiv.org_api_query_search_query_id_1811.06024'))
        m.register_uri('GET', 'http://harvest.aps.org/v2/journals/articles/10.1103/PhysRevD.99.045009',
                       request_headers={'Accept': 'application/pdf'},
                       content=read_response('article_upload', 'harvest.aps.org_PhysRevD.99.045009.pdf'))
        m.register_uri('GET', 'http://harvest.aps.org/v2/journals/articles/10.1103/PhysRevD.99.045009',
                       request_headers={'Accept': 'text/xml'},
                       content=read_response('article_upload', 'harvest.aps.org_PhysRevD.99.045009.xml'))
        m.get('https://api.crossref.org/works/10.1103/PhysRevD.99.045009',
              content=read_response('article_upload', 'crossref.org_works_10.1103_PhysRevD.99.045009'))
        workflow = run_workflow('aps.json', m)

    assert workflow.status == WorkflowStatus.COMPLETED
    assert Workflow.query.count() - workflows_count == 1

    record = _get_record_from_workflow(workflow)
    assert len(record['_files']) == 2


def test_elsevier():
    workflows_count = Workflow.query.count()

    with requests_mock.Mocker() as m:
        m.get('https://api.crossref.org/works/10.1016/j.nuclphysb.2018.07.004',
              content=read_response('article_upload', 'crossref.org_works_10.1016_j.nuclphysb.2018.07.004'))
        workflow = run_workflow('elsevier/elsevier.json', m)

    assert workflow.status == WorkflowStatus.COMPLETED
    assert Workflow.query.count() - workflows_count == 1

    record = _get_record_from_workflow(workflow)
    assert len(record['_files']) == 2


def test_springer():
    workflows_count = Workflow.query.count()

    with requests_mock.Mocker() as m:
        m.get('http://export.arxiv.org/api/query?search_query=id:1810.09837',
              content=read_response('article_upload', 'export.arxiv.org_api_query_search_query_id:1810.09837'))
        m.get('https://api.crossref.org/works/10.1140/epjc/s10052-019-6572-3',
              content=read_response('article_upload', 'crossref.org_works_10.1140_epjc_s10052-019-6572-3'))
        workflow = run_workflow('springer/springer.json', m)

    assert workflow.status == WorkflowStatus.COMPLETED
    assert Workflow.query.count() - workflows_count == 1

    record = _get_record_from_workflow(workflow)
    assert len(record['_files']) == 2


def test_oup():
    workflows_count = Workflow.query.count()

    with requests_mock.Mocker() as m:
        m.get('http://export.arxiv.org/api/query?search_query=id:1611.10151',
              content=read_response('article_upload', 'export.arxiv.org_api_query_search_query_id:1611.10151'))
        m.get('https://api.crossref.org/works/10.1093/ptep/pty143',
              content=read_response('article_upload', 'crossref.org_works_10.1093_ptep_pty143'))
        workflow = run_workflow('oup/oup.json', m)

    assert workflow.status == WorkflowStatus.COMPLETED
    assert Workflow.query.count() - workflows_count == 1

    record = _get_record_from_workflow(workflow)
    assert len(record['_files']) == 3
