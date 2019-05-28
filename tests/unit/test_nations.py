from invenio_db import db

from scoap3.dojson.utils.nations import find_country
from scoap3.modules.analysis.models import CountryCache


def test_countries():
    test_affs = (
        ('CMS CERN Switzerland', 'CERN'),
        ('ETH Switzerland', 'Switzerland'),
        ('CMS CERN KEK', 'CERN'),
        ('KEK Japan', 'Japan'),
        ('Hungary University of Magic and Witchcraft', 'Hungary'),
        ('Rome', 'Italy'),
        ('Ankara', 'Turkey'),
    )

    for test in test_affs:
        assert(find_country(test[0]) == test[1])


def test_cache():
    test_country_key = "some cached value2"

    # make sure there is no cache for this key yet
    existing_cc = CountryCache.query.get(test_country_key)
    if existing_cc:
        db.session.delete(existing_cc)
        db.session.commit()

    test_country_value = "Noland"
    cc = CountryCache()
    cc.key = test_country_key
    cc.country = test_country_value
    db.session.add(cc)
    db.session.commit()

    assert(find_country(test_country_key) == test_country_value)
