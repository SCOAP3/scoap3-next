class SCOAP3Robotupload(object):
    """Scoap3Records extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        app.extensions['scoap3-robotupload'] = self
