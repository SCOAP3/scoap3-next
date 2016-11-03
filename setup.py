# -*- coding: utf-8 -*-

"""scoap3 Invenio instance."""

import os

from setuptools import find_packages, setup

# Get the version string. Cannot be done with import!
version = {}
with open(os.path.join('scoap3',
                       'version.py'), 'rt') as fp:
    exec(fp.read(), version)

install_requires = [
    'invenio-config',
    'invenio-base',
    'invenio-access',
    'invenio-assets',
    'invenio-db',
    'invenio-indexer',
    'invenio-jsonschemas',
    'invenio-oaiharvester',
    'invenio-pidstore',
    'invenio-records',
    'invenio-records-rest',
    'invenio-records-ui',
    'invenio-search',
    'invenio-search-ui',
    'invenio-collections',
    'invenio-theme',
    'idutils',
    'invenio-workflows',
    'invenio-workflows-files',
    'invenio-workflows-ui',
],

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
        'invenio_base.apps': [
            'scoap3_records = scoap3.modules.records:Scoap3Records',
        ],
        'invenio_base.api_apps': [
            'scoap3_records = scoap3.modules.records:Scoap3Records',
        ],
        'invenio_base.blueprints': [
            'scoap3_search = scoap3.modules.search.views:blueprint',
            'scoap3_theme = scoap3.modules.theme.views:blueprint',
            'scoap3_frontpage = scoap3.modules.frontpage.views:blueprint'
        ],
        'invenio_assets.bundles': [
            'scoap3_theme_css = scoap3.modules.theme.bundles:css',
            'scoap3_search_js = scoap3.modules.theme.bundles:search_js',
            'scoap3_js = scoap3.modules.theme.bundles:js',
        ],
        'dojson.cli.rule': [
            'hep = scoap3.dojson.hep:hep',
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
            'records = scoap3.modules.records.mappings',
            'holdingpen = scoap3.modules.workflows.mappings'
        ],
        'invenio_workflows.workflows': [
            'sample = scoap3.modules.workflows.workflows:Sample1',
        ],
    },
    install_requires=install_requires,
)
