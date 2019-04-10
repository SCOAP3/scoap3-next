# -*- coding: utf-8 -*-

"""scoap3."""

from __future__ import absolute_import, print_function

from scoap3.cli_fixes import fixdb
from scoap3.cli_harvest import harvest
from scoap3.modules.compliance.cli import compliance
from scoap3.modules.records.cli import loadrecords

from .version import __version__


class Scoap3(object):
    """Scoap3 extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        app.extensions['scoap3'] = self
        app.cli.add_command(fixdb)
        app.cli.add_command(compliance)
        app.cli.add_command(loadrecords)
        app.cli.add_command(harvest)
        return self


__all__ = ('__version__', 'Scoap3',)
