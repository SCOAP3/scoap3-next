from __future__ import absolute_import, print_function


from .cli import loadrecords


class Scoap3Records(object):
    """Scoap3Records extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        app.extensions['scoap3-records'] = self
        app.cli.add_command(loadrecords)
        return self
