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
    'invenio-assets>=1.0.0a4',
    'invenio-db>=1.0.0a9',
    'invenio-indexer>=1.0.0a2',
    'invenio-jsonschemas>=1.0.0a2',
    'invenio-marc21>=1.0.0a1',
    'invenio-oaiserver>=1.0.0a1',
    'invenio-pidstore>=1.0.0a6',
    'invenio-records',
    'invenio-records-rest>=1.0.0a11',
    'invenio-records-ui>=1.0.0a4',
    'invenio-search>=1.0.0a7',
    'invenio-search-ui>=1.0.0a5',
],

setup(
    name='SCOAP3 Repository',
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
            'scoap3_frontpage = scoap3.modules.frontpage.views:blueprint',
        ],
        'invenio_assets.bundles': [
            'scoap3_search_js = scoap3.modules.theme.bundles:search_js',
        ],
        'dojson.cli.rule': [
            'hep = scoap3.dojson.hep:hep',
        ],
        'invenio_pidstore.minters': [
            'scoap3_recid_minter = scoap3.modules.pidstore.minters:scoap3_recid_minter',
        ],

        'invenio_pidstore.fetchers': [
            'scoap3_recid_fetcher = scoap3.modules.pidstore.fetchers:scoap3_recid_fetcher',
        ],
        'invenio_jsonschemas.schemas': [
            'scoap3_records = scoap3.modules.records.jsonschemas',
        ],
    },
    install_requires=install_requires,
)
