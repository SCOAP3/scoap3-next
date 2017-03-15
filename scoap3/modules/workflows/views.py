from flask import Blueprint

blueprint = Blueprint(
    'scoap3_workflows',
    __name__,
    url_prefix="/callback",
    template_folder='templates',
    static_folder="static",
)
