import logging
from datetime import datetime
from os import makedirs
from os.path import join, isdir

from flask import url_for, current_app
from inspire_dojson import marcxml2record

from scoap3.modules.robotupload.errorhandler import InvalidUsage

logger = logging.getLogger(__name__)


def save_package(package_name, file_data):
    # save delivered package for history
    save_path = current_app.config.get('ROBOTUPLOAD_FOLDER')
    if save_path:
        if not isdir(save_path):
            makedirs(save_path)

        package_path = join(save_path, package_name)
        with open(package_path, 'w') as f:
            f.write(file_data)
            logger.info('Robotupload package saved path=%s' % package_path)


def parse_received_package(file_data, package_name):
    """Parses received MarcXML data, also applies the needed mappings."""

    # Delete XML header if exists. Dojson library will call lxml.etree.parse on a decoded string,
    # which results in 'ValueError: Unicode strings with encoding declaration are not supported.'
    file_data = file_data.replace('<?xml version="1.0" encoding="UTF-8"?>', '')
    try:
        obj = marcxml2record(file_data)
    except Exception as e:
        logger.error('Marcxml parsing failed for package %s: %s' % (package_name, e))
        raise InvalidUsage("MARCXML is not valid.")

    obj['$schema'] = url_for('invenio_jsonschemas.get_schema', schema_path="hep.json")

    if 'self' in obj:
        del obj['self']

    _add_additional_info(obj)

    return obj


def _add_additional_info(obj):
    # map journal title and save new value.
    journal_title = obj['publication_info'][0]['journal_title']
    journal_title = current_app.config.get('JOURNAL_TITLE_MAPPING').get(journal_title, journal_title)
    obj['publication_info'][0]['journal_title'] = journal_title

    # get publisher based on journal title
    publisher = current_app.config.get('JOURNAL_PUBLISHER_MAPPING').get(journal_title)

    # add publisher if not exists
    if 'imprints' in obj and 'publisher' not in obj['imprints'][0]:
        obj['imprints'][0]['publisher'] = publisher

    # add creation date if not exists
    if 'record_creation_date' not in obj:
        obj['record_creation_date'] = datetime.now().isoformat()

    # add acquisition_source if not exists
    if 'acquisition_source' not in obj:
        obj['acquisition_source'] = {
            'source': publisher or 'scoap3_push',
            'method': 'scoap3_push',
            'date': datetime.now().isoformat()
        }

    # add material if not exists
    if 'material' not in obj['publication_info'][0] and 'document_type' in obj:
        obj['publication_info'][0]['material'] = obj['document_type'][0]

    # remove document type, it should be in publication_info as material
    if 'document_type' in obj:
        del obj['document_type']
