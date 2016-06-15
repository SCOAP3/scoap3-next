# -*- coding: utf-8 -*-

"""scoap3 base Invenio configuration."""

from __future__ import absolute_import, print_function


# Identity function for string extraction
def _(x):
    return x

# Default language and timezone
BABEL_DEFAULT_LANGUAGE = 'en'
BABEL_DEFAULT_TIMEZONE = 'Europe/Zurich'
I18N_LANGUAGES = [
]

HEADER_TEMPLATE = "scoap3_theme/header.html"
BASE_TEMPLATE = "scoap3_theme/page.html"
COVER_TEMPLATE = "invenio_theme/page_cover.html"
SETTINGS_TEMPLATE = "invenio_theme/settings/content.html"

# WARNING: Do not share the secret key - especially do not commit it to
# version control.
SECRET_KEY = "5EeAQcsqST1J6U7dTlQsBsJMcAuMgqdbfvut9YoDw75fRTlnQ7OtMcNcfp4OzOtQUUsVFWThN5YmJ023XzKHOMcMZIEblxgyoMSkyP5rcnlBCQ4yJOCBsXxmn13RxcK7yQ7U996ey59zce1i47VoVTyk1wwOKJocafnyOk4HfcE3Xx2IxKQYk8EXWtPVlndmVZZuba9kivA73QfWB9uxumFd8wtMhLm6quRa8KB9eqywNyCwcz6DHGYQzRKKvtgo"

# Theme
THEME_SITENAME = _("scoap3")
ASSETS_DEBUG = True
COLLECT_STORAGE = "flask_collect.storage.link"
