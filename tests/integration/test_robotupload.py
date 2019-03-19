import re
from os import path

import requests_mock
from flask import current_app
from mock import patch
from invenio_workflows import Workflow
from workflow.engine_db import WorkflowStatus

from scoap3.modules.robotupload.views import handle_upload_request
from tests.responses import get_response_dir


title_schema = '{"$schema": "http://json-schema.org/schema#", "uniqueItems": true, "items": {"type": "object", "properties": {"source": {"type": ["string","null"]}, "subtitle": {"type": ["string","null"]}, "title": {"type": "string"}}, "title": "Title (and subtitle)"}, "type": "array"}'  # noqa


def _read_file(input_filename):
    file_path = path.join(get_response_dir(), 'robotupload', input_filename)
    with open(file_path, 'rb') as f:
        return f.read()


def run_workflow(input_filename):
    """Use input_filename to build request and to run article_upload workflow."""

    # build request mock
    class RequestMock():
        class MockFile():
            def __init__(self):
                # read request data
                self.file_data = _read_file(input_filename)

            filename = input_filename

            def read(self):
                # read once to mimic original stream behaviour
                result = self.file_data
                self.file_data = ''
                return result

        headers = {'User-Agent': 'invenio_webupload', 'Host': 'localhost'}
        environ = {'REMOTE_ADDR': '127.0.0.1'}
        args = {}
        files = {
            'file': MockFile()
        }

    # run workflow with patched request
    with patch('scoap3.modules.robotupload.views.request', RequestMock()), \
            patch.dict(current_app.config, ROBOTUPLOAD_FOLDER='/tmp/'):
        workflow_id = handle_upload_request(apply_async=False)[0]
        return Workflow.query.get(workflow_id)


def test_robotupload_cpc():
    with requests_mock.Mocker() as m:
        pdf_data = _read_file('scoap3_iop_org_0131004.pdf')
        xml_data = _read_file('scoap3_iop_org_0131004.xml')
        arxiv_data = _read_file('1805.03803.xml')
        crossref_data = _read_file('crossref_10.1088_1674-1137_43_1_013104.json')
        m.get('http://scoap3.iop.org/article/doi/10.1088/1674-1137/43/1/013104?format=pdf', content=pdf_data)
        m.get('http://scoap3.iop.org/article/doi/10.1088/1674-1137/43/1/013104?format=xml', content=xml_data)
        m.get('http://export.arxiv.org/api/query?search_query=id:1805.03803', content=arxiv_data)
        m.get('http://beta.scoap3.org/schemas/elements/titles.json', text=title_schema)
        m.get('https://api.crossref.org/works/10.1088/1674-1137/43/1/013104', text=crossref_data)
        m.register_uri(
            requests_mock.ANY,
            re.compile('.*(indexer).*'),
            real_http=True,
        )

        workflows_count = Workflow.query.count()
        workflow = run_workflow('batchupload_20190102132204_4AEY6N_cpc.xml')
        assert workflow.status == WorkflowStatus.COMPLETED

        # test if only one workflow was created
        assert Workflow.query.count() - workflows_count == 1


def test_robotupload_acta():
    with requests_mock.Mocker() as m:
        pdfa_data = _read_file('actaphys.pdf')
        pdf_data = _read_file('actaphys.pdf')
        arxiv_data = _read_file('1812.04746.xml')
        crossref_data = _read_file('crossref_10.5506_APhysPolB.50.37.json')
        m.get('http://www.actaphys.uj.edu.pl/fulltext?series=reg&vol=50&page=37&fmt=pdfa', content=pdfa_data)
        m.get('http://www.actaphys.uj.edu.pl/fulltext?series=reg&vol=50&page=37', content=pdf_data)
        m.get('http://export.arxiv.org/api/query?search_query=id:1812.04746', text=arxiv_data)
        m.get('https://api.crossref.org/works/10.5506/APhysPolB.50.37', text=crossref_data)
        m.get('http://beta.scoap3.org/schemas/elements/titles.json', text=title_schema)
        m.register_uri(
            requests_mock.ANY,
            re.compile('.*(indexer).*'),
            real_http=True,
        )

        workflows_count = Workflow.query.count()
        workflow = run_workflow('batchupload_20190125120350_PuCDSV_acta.xml')
        assert workflow.status == WorkflowStatus.COMPLETED

        # test if only one workflow was created
        assert Workflow.query.count() - workflows_count == 1
