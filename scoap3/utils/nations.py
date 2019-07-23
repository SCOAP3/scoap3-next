# -*- coding: utf-8 -*-

import re

from scoap3.config import COUNTRIES_DEFAULT_MAPPING
from scoap3.utils.google_maps import get_country


# when there is a lot of affiliations caching the result speeds up the process.
country_cache = {}


def find_country(affiliation):
    if affiliation not in country_cache:
        country_cache[affiliation] = _find_country_no_cache(affiliation)

    return country_cache[affiliation]


def _find_country_no_cache(affiliation):
    for key, val in COUNTRIES_DEFAULT_MAPPING.iteritems():
        if re.search(r'\b%s\b' % key, affiliation, flags=re.IGNORECASE):
            return val

    # if we can't figure out the country use the cache and Google API if needed
    return get_country(affiliation) or "HUMAN CHECK"
