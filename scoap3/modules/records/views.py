from flask import Blueprint

blueprint = Blueprint(
    'scoap3_records',
    __name__,
    template_folder='templates',
)
