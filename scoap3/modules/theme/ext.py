from .views import blueprint

class SCOAP3Theme(object):
    """Invenio theme extension."""

    def __init__(self, app=None, **kwargs):
        """Extension initialization."""

        app.name = "SCOAP3Theme"

        if app:
            app.register_blueprint(blueprint)
            app.jinja_env.add_extension('jinja2.ext.do')
            app.extensions['inspire-theme'] = self
