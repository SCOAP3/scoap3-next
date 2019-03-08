from mock import patch
from pytest import raises

from scoap3.modules.robotupload.errorhandler import InvalidUsage
from scoap3.modules.robotupload.views import check_permission_for_journal, validate_request


class MockApp():
    def __init__(self, config):
        self.config = config


def call_check_perms(journal_title, allowed_users, remote_addr):
    package_name = 'dummy'  # only used for logging
    with patch('scoap3.modules.robotupload.views.current_app', MockApp(dict(ROBOTUPLOAD_ALLOWED_USERS=allowed_users))):
        check_permission_for_journal(journal_title, remote_addr, package_name)


def test_check_perm_valid():
    journal_title = 'JournalK'
    allowed_users = {'127.0.0.1': ['JournalK'], }
    remote_addr = '127.0.0.1'
    call_check_perms(journal_title, allowed_users, remote_addr)


def test_check_perm_valid_all():
    journal_title = 'JournalK'
    allowed_users = {'127.0.0.1': ['ALL'], }
    remote_addr = '127.0.0.1'
    call_check_perms(journal_title, allowed_users, remote_addr)


def test_check_perm_invalid_no_journal():
    journal_title = ''
    allowed_users = {'127.0.0.1': ['ALL'], }
    remote_addr = '1.1.1.1'
    with raises(InvalidUsage):
        call_check_perms(journal_title, allowed_users, remote_addr)


def test_check_perm_invalid_ip():
    journal_title = 'JournalK'
    allowed_users = {'127.0.0.1': ['ALL'], }
    remote_addr = '1.1.1.1'
    with raises(InvalidUsage):
        call_check_perms(journal_title, allowed_users, remote_addr)


def test_check_perm_invalid_journal():
    journal_title = 'Different journal'
    allowed_users = {'127.0.0.1': ['JournalK'], }
    remote_addr = '127.0.0.1'
    with raises(InvalidUsage):
        call_check_perms(journal_title, allowed_users, remote_addr)


class MockFile():
    def __init__(self, filename):
        self.filename = filename


class MockRequest():
    def __init__(self, filename=None):
        self.files = dict(file=MockFile(filename)) if filename else dict()


def call_validate_request(remote_addr, allowed_users, request):
    exts = ['xml']
    config = dict(ROBOTUPLOAD_ALLOWED_USERS=allowed_users, ROBOTUPLOAD_ALLOWED_EXTENSIONS=exts)
    with patch('scoap3.modules.robotupload.views.current_app', MockApp(config)),\
            patch('scoap3.modules.robotupload.views.request', request):
        validate_request(remote_addr)


def test_validate_valid():
    remote_addr = '2.2.2.2'
    allowed_users = {'2.2.2.2': ['ALL'], }
    call_validate_request(remote_addr, allowed_users, MockRequest('data.xml'))


def test_validate_invalid_ip():
    remote_addr = '1.1.1.1'
    allowed_users = {'2.2.2.2': ['ALL'], }

    with raises(InvalidUsage):
        call_validate_request(remote_addr, allowed_users, MockRequest('data.xml'))


def test_validate_invalid_nofile():
    remote_addr = '2.2.2.2'
    allowed_users = {'2.2.2.2': ['ALL'], }

    with raises(InvalidUsage):
        call_validate_request(remote_addr, allowed_users, MockRequest())


def test_validate_invalid_extension():
    remote_addr = '2.2.2.2'
    allowed_users = {'2.2.2.2': ['ALL'], }

    with raises(InvalidUsage):
        call_validate_request(remote_addr, allowed_users, MockRequest('my.py'))
