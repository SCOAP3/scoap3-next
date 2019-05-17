from flask import current_app


def dumps_etree(pid, record, **kwargs):
    """Dump MARC21 compatible record.
    :param pid: The :class:`invenio_pidstore.models.PersistentIdentifier`
        instance.
    :param record: The :class:`invenio_records.api.Record` instance.
    :returns: A LXML Element instance.
    """
    from scoap3.dojson.hep.model import hep2marc
    from scoap3.dojson.dump_utils import dumps_etree

    r = record['_source']

    # create and add download url
    if 'urls' not in r and '_files' in r:
        files = []
        for f in r['_files']:
            url = 'http://%s/api/files/%s/%s' % (current_app.config.get('SERVER_NAME'), f['bucket'], f['key'])
            files.append({
                'value': url,
                'description': f['filetype']
            })
        r['urls'] = files

    return dumps_etree(hep2marc.do(r), **kwargs)
