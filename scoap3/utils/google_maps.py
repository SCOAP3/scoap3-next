from flask import current_app
from invenio_db import db
from sqlalchemy import func
from sqlalchemy.orm.exc import NoResultFound

from scoap3.config import COUNTRIES_DEFAULT_MAPPING
from scoap3.modules.analysis.models import CountryCache
from scoap3.utils.http import requests_retry_session


def get_country(text):
    """
    Tries to find the country for the given text. It can use multiple Google API calls to decide.
    If the query was successful we store the result in the cache.
    Returns None if can't determine.
    """

    try:
        return CountryCache.query.filter(func.lower(CountryCache.key) == text.lower()).one().country
    except NoResultFound:
        # try with different subsets of the affiliation if we can't find a match at first
        country = __get_country(text) or __get_country(text.split(',')[-1]) or __get_country(' '.join(text.split(',')[-2:]))

    if country:
        cc = CountryCache()
        cc.key = text
        cc.country = country
        db.session.add(cc)
        db.session.commit()

    return country


def __get_country(search_text):
    """Return the country of the search text based on Google Maps."""

    GOOGLE_MAPS_API_URL = 'https://maps.googleapis.com/maps/api/geocode/json'

    params = {
        'address': search_text,
        'language': 'en',
        'key': current_app.config.get('GOOGLE_API_KEY', '')
    }

    req = requests_retry_session().get(GOOGLE_MAPS_API_URL, params=params, timeout=1).json()

    if 'status' in req:
        if req['status'].lower() == 'ok':
            country = __get_country_from_results(req)
            return COUNTRIES_DEFAULT_MAPPING.get(country, country)

    return None


def __get_country_from_results(results):
    if 'results' in results:
        for address_component in results['results'][0]['address_components']:
            if 'country' in address_component['types']:
                return address_component['long_name']

    return None
