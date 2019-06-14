import logging
from datetime import datetime

from flask import current_app

from scoap3.utils.http import requests_retry_session


logger = logging.getLogger(__name__)


def parse_date_parts(parts):
    # if we don't have month or day substitute it with 1
    if len(parts) < 3:
        parts.extend([1] * (3 - len(parts)))
    return datetime(*parts)


def get_crossref_items(filter_param=None):
    crossref_url = current_app.config.get('CROSSREF_API_URL')

    params = {
        'filter': filter_param,
        'cursor': '*'
    }

    while True:
        api_response = requests_retry_session().get(crossref_url, params=params)

        if api_response.status_code != 200:
            logger.error('Failed to query crossref. params' % params)
            break

        message = api_response.json()['message']

        items = message.get('items')
        if not items:
            break

        for item in items:
            yield item

        params['cursor'] = message.get('next-cursor')
