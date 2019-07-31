from dateutil.parser import parse as parse_date
from flask import current_app
from inspire_dojson import record2marcxml
from inspire_utils.record import get_value
from lxml import etree


def dumps_etree(pid, record, **kwargs):
    """Dump MARC21 compatible record.
    :param pid: The :class:`invenio_pidstore.models.PersistentIdentifier`
        instance.
    :param record: The :class:`invenio_records.api.Record` instance.
    :returns: A LXML Element instance.
    """

    r = record['_source']

    # adding legacy version (controlfield 005)
    acquisition_date = parse_date(r['acquisition_source']['date'])
    r['legacy_version'] = acquisition_date.strftime("%Y%m%d%H%M%S.0")

    # adding number of pages (datafield 300)
    page_nr = get_value(r, 'page_nr[0]')
    if page_nr:
        r['number_of_pages'] = page_nr

    # create and add download url
    if 'urls' not in r and '_files' in r:
        files = []
        for f in r['_files']:
            url = 'http://%s/api/files/%s/%s' % (current_app.config.get('SERVER_NAME'), f['bucket'], f['key'])
            files.append({
                'value': url,
                'description': f.get('filetype', '')
            })
        r['urls'] = files

    return etree.fromstring(record2marcxml(r))
