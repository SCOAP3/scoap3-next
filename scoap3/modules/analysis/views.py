from flask import Blueprint

blueprint = Blueprint(
    'scoap3_analysis',
    __name__,
    url_prefix='',
    template_folder='templates',
)
