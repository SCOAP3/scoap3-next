from scoap3.modules.records.admin import RecordsDashboard
from mock import patch


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
