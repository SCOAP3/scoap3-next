# -*- coding: utf-8 -*-

from scoap3.config import COUNTRIES_DEFAULT_MAPPING
from scoap3.utils.google_maps import get_country


def find_country(affiliation):
    affiliation = affiliation.lower()

    for key, val in COUNTRIES_DEFAULT_MAPPING.iteritems():
        if key.lower() in affiliation:
            return val

    # if we can't figure out the country use the cache and Google API if needed
    return get_country(affiliation) or "HUMAN CHECK"
