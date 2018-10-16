from flask import Blueprint

blueprint = Blueprint(
    'scoap3_compliance',
    __name__,
    url_prefix='/compliance',
    template_folder='templates',
)
