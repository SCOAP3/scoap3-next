from invenio_oauth2server.models import Scope

harvesting_read = Scope('harvesting:read',
                        help_text='Access to the haresting',
                        group='test')
