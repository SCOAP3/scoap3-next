import re
from os.path import join

import requests_mock
from flask import current_app
from mock import patch
from invenio_workflows import Workflow
from workflow.engine_db import WorkflowStatus

from scoap3.modules.robotupload.views import handle_upload_request
from tests.integration.utils import mock_halt
from tests.responses import get_response_dir, read_response


def load_schema(name):
    with open(join(get_response_dir(), 'jsonschemas', name), 'rb') as f:
        return f.read()


def run_workflow(input_filename, request_mock):
    """Use input_filename to build request and to run article_upload workflow."""

    # build request mock
    class RequestMock():
        def __init__(self):
            self.data = read_response('robotupload', input_filename)

        headers = {'User-Agent': 'invenio_webupload', 'Host': 'localhost'}
        environ = {'REMOTE_ADDR': '127.0.0.1'}
        args = {}

    # run workflow with patched request
    with patch('scoap3.modules.robotupload.views.request', RequestMock()), \
            patch('scoap3.modules.workflows.workflows.articles_upload.__halt_and_notify', mock_halt), \
            patch.dict(current_app.config, ROBOTUPLOAD_FOLDER='/tmp/'):

        title_schema = load_schema(join('elements', 'titles.json'))
        hep_schema = load_schema('hep.json')
        request_mock.register_uri('GET', '/schemas/hep.json', content=hep_schema)
        request_mock.register_uri('GET', '/schemas/elements/titles.json', content=title_schema)
        request_mock.register_uri(
            requests_mock.ANY,
            re.compile('.*(indexer).*'),
            real_http=True,
        )

        workflow_id = handle_upload_request(apply_async=False)[0]
        return Workflow.query.get(workflow_id)


def test_robotupload_cpc():
    with requests_mock.Mocker() as m:
        pdf_data = read_response('robotupload', 'scoap3_iop_org_0131004.pdf')
        xml_data = read_response('robotupload', 'scoap3_iop_org_0131004.xml')
        arxiv_data = read_response('robotupload', '1805.03803.xml')
        crossref_data = read_response('robotupload', 'crossref_10.1088_1674-1137_43_1_013104.json')
        m.get('http://scoap3.iop.org/article/doi/10.1088/1674-1137/43/1/013104?format=pdf', content=pdf_data)
        m.get('http://scoap3.iop.org/article/doi/10.1088/1674-1137/43/1/013104?format=xml', content=xml_data)
        m.get('http://export.arxiv.org/api/query?search_query=id:1805.03803', content=arxiv_data)
        m.get('https://api.crossref.org/works/10.1088/1674-1137/43/1/013104', text=crossref_data)

        workflows_count = Workflow.query.count()
        workflow = run_workflow('batchupload_20190102132204_4AEY6N_cpc.xml', m)
        assert workflow.status == WorkflowStatus.COMPLETED

        # test if only one workflow was created
        assert Workflow.query.count() - workflows_count == 1


def test_robotupload_acta():
    with requests_mock.Mocker() as m:
        pdfa_data = read_response('robotupload', 'actaphys.pdf')
        pdf_data = read_response('robotupload', 'actaphys.pdf')
        arxiv_data = read_response('robotupload', '1812.04746.xml')
        crossref_data = read_response('robotupload', 'crossref_10.5506_APhysPolB.50.37.json')
        m.get('http://www.actaphys.uj.edu.pl/fulltext?series=reg&vol=50&page=37&fmt=pdfa', content=pdfa_data)
        m.get('http://www.actaphys.uj.edu.pl/fulltext?series=reg&vol=50&page=37', content=pdf_data)
        m.get('http://export.arxiv.org/api/query?search_query=id:1812.04746', text=arxiv_data)
        m.get('https://api.crossref.org/works/10.5506/APhysPolB.50.37', text=crossref_data)

        workflows_count = Workflow.query.count()
        workflow = run_workflow('batchupload_20190125120350_PuCDSV_acta.xml', m)
        assert workflow.status == WorkflowStatus.COMPLETED

        # test if only one workflow was created
        assert Workflow.query.count() - workflows_count == 1
