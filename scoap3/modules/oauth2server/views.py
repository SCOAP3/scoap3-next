from __future__ import absolute_import, print_function

from invenio_oauth2server.decorators import require_api_auth, require_oauth_scopes
from flask import Blueprint

blueprint = Blueprint(
    'scoap3_oauth2server',
    __name__,
    url_prefix='/oauth2server',
)


@blueprint.route('/test_scope')
@require_api_auth()
@require_oauth_scopes('harvesting:read')
def index():
    return "OK!"
