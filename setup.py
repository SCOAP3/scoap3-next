# -*- coding: utf-8 -*-

"""scoap3 Invenio instance."""

import os

from setuptools import find_packages, setup

# Get the version string. Cannot be done with import!
version = {}
with open(os.path.join('scoap3',
                       'version.py'), 'rt') as fp:
    exec(fp.read(), version)

install_requires = (
    'arrow~=0.13.0',
    'celery<4.0',
    'idutils',
    'inspire-crawler~=1.0',
    'inspire-dojson~=61.1.11',
    'inspire-utils>=3.0.3',
    'invenio-access~=1.0.1',
    'invenio-accounts~=1.0.2',
    'invenio-admin~=1.1.1',
    'invenio-assets~=1.1.2',
    'invenio-base~=1.0.2',
    'invenio-config~=1.0.1',
    'invenio-db[postgresql,versioning]~=1.0.3',
    'invenio-files-rest>=1.0.0a23',
    'invenio-indexer~=1.0.2',
    'invenio-jsonschemas>=1.0.0a5',
    'invenio-logging~=1.1.1',
    'invenio-mail~=1.0.2',
    'invenio-oaiharvester==1.0.0a4',
    'invenio-oaiserver==1.0.3',
    'invenio-oauth2server~=1.0.3',
    'invenio-oauthclient~=1.1.2',
    'invenio-pidstore~=1.0.0',
    'invenio-records==1.0.0',
    'invenio-records-rest~=1.4.2',
    'invenio-records-ui==1.0.0b2',
    'invenio-records-files==1.0.0a11',
    'invenio-search-ui==1.0.1',
    'invenio-theme==1.0.0b2',
    'invenio-workflows~=7.0.3',
    'invenio-workflows-files~=1.0',
    # FIXME 'invenio-workflows-ui~=2.0.15',
    'invenio-workflows-ui @ git+http://github.com/SCOAP3/invenio-workflows-ui@es7#egg=invenio-workflows-ui',
    'Flask-Admin>=1.5.3',
    'urllib3==1.23',
    'jsonschema~=2.6.0',
)

tests_require = (
    'freezegun~=0.3,>=0.3.11',
)

extras_require = {
    'tests': tests_require,
    'all': install_requires + tests_require
}

setup(
    name='scoap3',
    version=version['__version__'],
    description=__doc__,
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'console_scripts': [
            'scoap3 = scoap3.cli:cli',
        ],
        'invenio_admin.views': [
            'scoap3_api_registrations = scoap3.modules.api.admin:api_registrations_adminview',
            'scoap3_gdp = scoap3.modules.analysis.admin:gdp_adminview',
            'scoap3_analysis_gdp_import = scoap3.modules.analysis.admin:gdpimport_adminview',
            'scoap3_articleimpact = scoap3.modules.analysis.admin:articleimpact_adminview',
            'scoap3_countriesshare = scoap3.modules.analysis.admin:countriesshare_view',
            'scoap3_workflows = scoap3.modules.workflows.admin:workflows',
            'scoap3_workflows_summary = scoap3.modules.workflows.admin:workflows_summary',
            'scoap3_compliance = scoap3.modules.compliance.admin:compliance_adminview',
            'invenio_records = scoap3.modules.records.admin:record_adminview',
            'scoap3_records_dashboard = scoap3.modules.records.admin:record_dashboard',
        ],
        'invenio_base.apps': [
            'scoap3 = scoap3:Scoap3',
            'scoap3_workflows = scoap3.modules.workflows:SCOAP3Workflows',
            'scoap3_robotupload = scoap3.modules.robotupload:SCOAP3Robotupload',
        ],
        'invenio_base.api_blueprints': [
            'scoap3_oauth2server = scoap3.modules.oauth2server.views:blueprint',
        ],
        'invenio_base.blueprints': [
            'scoap3_search = scoap3.modules.search.views:blueprint',
            'scoap3_theme = scoap3.modules.theme.views:blueprint',
            'scoap3_frontpage = scoap3.modules.frontpage.views:blueprint',
            'scoap3_accounts = scoap3.modules.accounts.views:blueprint',
            'scoap3_workflows = scoap3.modules.workflows.views:blueprint',
            'scoap3_robotupload = scoap3.modules.robotupload.views:blueprint',
            'scoap3_api = scoap3.modules.api.views:blueprint',
            'scoap3_compliance = scoap3.modules.compliance.views:blueprint',
            'scoap3_analysis = scoap3.modules.analysis.views:blueprint',
            'scoap3_tools = scoap3.modules.tools.views:blueprint',
            'scoap3_records = scoap3.modules.records.views:blueprint',
        ],
        'invenio_assets.bundles': [
            'scoap3_theme_css = scoap3.modules.theme.bundles:css',
            'scoap3_search_js = scoap3.modules.theme.bundles:search_js',
            'scoap3_js = scoap3.modules.theme.bundles:js',
        ],
        'invenio_db.alembic': [
            'scoap3_api = scoap3.modules.api:alembic',
            'scoap3_analysis = scoap3.modules.analysis:alembic',
            'scoap3_compliance = scoap3.modules.compliance:alembic',
        ],
        'invenio_db.models': [
            'scoap3_api = scoap3.modules.api.models',
            'scoap3_analysis = scoap3.modules.analysis.models',
            'scoap3_compliance = scoap3.modules.compliance.models',
        ],
        'invenio_pidstore.minters': [
            'scoap3_minter = scoap3.modules.pidstore.minters:scoap3_recid_minter',
        ],

        'invenio_pidstore.fetchers': [
            'scoap3_fetcher = scoap3.modules.pidstore.fetchers:scoap3_recid_fetcher',
        ],
        'invenio_jsonschemas.schemas': [
            'scoap3_records = scoap3.modules.records.jsonschemas',
        ],
        'invenio_search.mappings': [
            'scoap3-records = scoap3.modules.records.mappings',
            'scoap3-workflows = scoap3.modules.workflows.mappings'
        ],
        'invenio_workflows.workflows': [
            'articles_upload = scoap3.modules.workflows.workflows:ArticlesUpload',
            'run_compliance = scoap3.modules.workflows.workflows:RunCompliance',
        ],
        'invenio_celery.tasks': [
            'robotupload = scoap3.modules.robotupload.tasks',
            'analysis = scoap3.modules.analysis.tasks',
            'workflows = scoap3.modules.workflows.tasks',
            'records = scoap3.modules.records.tasks',
            'tools = scoap3.modules.tools.tasks',
        ],
        'invenio_oauth2server.scopes': [
            'harvesting_read = scoap3.modules.oauth2server.scopes:harvesting_read',
        ],
    },
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require=extras_require
)
