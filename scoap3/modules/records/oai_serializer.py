def dumps_etree(pid, record, **kwargs):
    """Dump MARC21 compatible record.
    :param pid: The :class:`invenio_pidstore.models.PersistentIdentifier`
        instance.
    :param record: The :class:`invenio_records.api.Record` instance.
    :returns: A LXML Element instance.
    """
    from scoap3.dojson.hep.model import hep2marc
    from scoap3.dojson.dump_utils import dumps_etree

    return dumps_etree(hep2marc.do(record['_source']), **kwargs)
