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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with INSPIRE. If not, see <http://www.gnu.org/licenses/>.
#
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

from __future__ import absolute_import, division, print_function

import os
import sys

import pytest
import requests_mock
from workflow.engine_db import WorkflowStatus

from scoap3.factory import create_app

from tests.integration.utils import get_record_from_workflow, run_article_upload_with_file
from tests.responses import read_response

# Use the helpers folder to store test helpers.
# See: http://stackoverflow.com/a/33515264/374865
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'helpers'))


@pytest.fixture(autouse=True, scope='session')
def app():
    """Flask application.
    Creates a Flask application with a simple testing configuration,
    then creates an application context and yields, so that all tests
    have access to one.
    See: http://flask.pocoo.org/docs/0.12/appcontext/.
    """
    app = create_app(
        DEBUG=False,
        # Tests may fail when turned on because of Flask bug (A setup function was called after the first request
        # was handled. when initializing - when Alembic initialization)
        WTF_CSRF_ENABLED=False,
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_RESULT_BACKEND='cache',
        CELERY_CACHE_BACKEND='memory',
        CELERY_TASK_EAGER_PROPAGATES=True,
        TESTING=True,
        PRODUCTION_MODE=True,
    )

    with app.app_context():
        yield app


@pytest.fixture(scope='function')
def app_client(app):
    """Flask test client for the application.
    See: http://flask.pocoo.org/docs/0.12/testing/#keeping-the-context-around.
    """
    with app.test_client() as client:
        yield client


@pytest.fixture(scope='session')
def api(app):
    """Flask API application."""
    yield app.wsgi_app.mounts['/api']


@pytest.fixture(scope='function')
def api_client(api):
    """Flask test client for the API application."""
    with api.test_client() as client:
        yield client


@pytest.fixture(scope='function')
def request_context(app):
    """Flask request context.
    See: http://flask.pocoo.org/docs/0.12/reqcontext/.
    """
    with app.test_request_context() as request_context:
        yield request_context


@pytest.fixture(scope='function')
def test_record():
    with requests_mock.Mocker() as m:
        m.get('https://api.crossref.org/works/10.1016/j.nuclphysb.2018.07.004',
              content=read_response('article_upload', 'crossref.org_works_10.1016_j.nuclphysb.2018.07.004'))
        workflow = run_article_upload_with_file('elsevier/elsevier.json', m)

    assert workflow.status == WorkflowStatus.COMPLETED

    return get_record_from_workflow(workflow)
