# -*- coding: utf-8 -*-

"""scoap3 Invenio WSGI application."""

from __future__ import absolute_import, print_function

from .factory import create_app

application = create_app()
