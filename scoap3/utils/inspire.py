from flask import current_app
from inspire_utils.record import get_value

from scoap3.utils.http import requests_retry_session


def get_inspire_records(query):
    url = current_app.config.get('INSPIRE_LITERATURE_API_URL')
    data = requests_retry_session().get(url, params={'q': query})

    return data.json()['hits']['hits']


def get_inspire_arxiv_categories_for_record(query):
    records = get_inspire_records(query)
    if len(records) == 1:
        return get_value(records[0], 'metadata.arxiv_eprints[0].categories')

    return None
