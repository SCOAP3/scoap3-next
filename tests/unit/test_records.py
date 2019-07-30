import json

from freezegun import freeze_time

from scoap3.modules.records.admin import RecordsDashboard
from mock import patch

from scoap3.modules.records.views import collections_count


def base_admin_article_check(from_date, expected_flash):
    with patch('scoap3.modules.records.tasks.perform_article_check.apply_async'), \
            patch('scoap3.modules.records.admin.flash') as flash:

        result = RecordsDashboard.run_article_check(from_date)

        flash.assert_called_once_with(*expected_flash)

    return result


def test_admin_article_check_no_date():
    flash = ('From date is required to run article check.', 'error')
    assert base_admin_article_check(None, flash) is False


def test_admin_article_check_only_year():
    flash = ('"2019" is invalid date parameter. It has to be in YYYY-mm-dd format.', 'error')
    assert base_admin_article_check('2019', flash) is False


def test_admin_article_check_year_month():
    flash = ('"2019-01" is invalid date parameter. It has to be in YYYY-mm-dd format.', 'error')
    assert base_admin_article_check('2019-01', flash) is False


def test_admin_article_check_invalid_date():
    flash = ('"2019-01-40" is invalid date parameter. It has to be in YYYY-mm-dd format.', 'error')
    assert base_admin_article_check('2019-01-40', flash) is False


def test_admin_article_check():
    flash = ("Article check started. The result will be sent out in an email.", 'success')
    assert base_admin_article_check('2019-01-01', flash) is True


class MockApp():
    def __init__(self, config):
        self.config = config


class MockES():
    es_data = {
        'journal:"Physical Review D"': 4,
        'journal:"European Physical Journal C"': 5,
        'journal:"Nuclear Physics B"': 6,
        'journal:"Physical Review C"': 7,

        "record_creation_date:>=2019-07-28": 3,
        "record_creation_date:>=2019-06-29": 10,
        "record_creation_date:>=2019": 20,
    }

    def count(self, q=None):
        return {'count': self.es_data.get(q)}


def test_collections_count():
    config = {"JOURNAL_ABBREVIATIONS": {
        "Physical Review D": "",
        "European Physical Journal C": "",
        "Nuclear Physics B": "",
        "Physical Review C": ""
    }}

    with patch('scoap3.modules.records.views.current_app', MockApp(config)), \
            patch('scoap3.modules.records.views.current_search_client', MockES()), \
            freeze_time('2019-07-29'):
        data = json.loads(collections_count().data)

        assert data["other"]["last_30_days"] == 10
        assert data["other"]["this_year"] == 20
        assert data["other"]["yesterday"] == 3
        assert data["other"]["all"] == 22
        assert data["journals"]["Physical Review D"] == 4
        assert data["journals"]["European Physical Journal C"] == 5
        assert data["journals"]["Nuclear Physics B"] == 6
        assert data["journals"]["Physical Review C"] == 7
