import mock
from invenio_db import db

from scoap3.modules.api.models import ApiRegistrations
from scoap3.modules.api.views import handler_registration


def test_basic():
    data = dict(
        email=u'test@example.com',
        partner='1',
        name='Test User',
        organization='CERN',
        role='Tester',
        country='Switzerland',
        description='-'
    )

    # make sure we don't already have a registration with this email
    for e in ApiRegistrations.query.filter(ApiRegistrations.email == data['email']).all():
        db.session.delete(e)

    m = mock.MagicMock()
    m.method = 'POST'
    m.form = data

    with mock.patch("scoap3.modules.api.views.request", m),\
            mock.patch("scoap3.modules.api.views.flash"):
        assert handler_registration() is True
        registration = ApiRegistrations.query.filter(ApiRegistrations.email == data['email']).one()

        assert registration.email == data['email']
        assert registration.partner is True
        assert registration.name == data['name']
        assert registration.organization == data['organization']
        assert registration.role == data['role']
        assert registration.country == data['country']
        assert registration.description == data['description']


def test_duplicate():
    email = u'test2@example.com'

    # make sure we don't already have a registration with this email
    for e in ApiRegistrations.query.filter(ApiRegistrations.email == email).all():
        db.session.delete(e)

    m = mock.MagicMock()
    m.method = 'POST'
    m.form = {
        'email': email,
    }

    with mock.patch("scoap3.modules.api.views.request", m),\
            mock.patch("scoap3.modules.api.views.flash"):
        assert handler_registration() is True
        assert ApiRegistrations.query.filter(ApiRegistrations.email == email).count() == 1
        assert handler_registration() is False


def test_no_email():
    email = ''

    m = mock.MagicMock()
    m.method = 'POST'
    m.form = {
        'email': email,
    }

    with mock.patch("scoap3.modules.api.views.request", m),\
            mock.patch("scoap3.modules.api.views.flash"):
        assert handler_registration() is False
