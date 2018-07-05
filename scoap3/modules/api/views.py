from __future__ import absolute_import, print_function

from flask import Blueprint, render_template

blueprint = Blueprint(
    'scoap3_api',
    __name__,
    url_prefix='/partners',
    template_folder='templates',
    static_folder='static',
)


@blueprint.route('/')
def index():
    return render_template(
        'scoap3_api/index.html',
        title='SCOAP3 Repository - API'
    )


@blueprint.route('/register', ['GET', 'POST'])
def register():
    return render_template(
        'scoap3_api/register.html',
        title='SCOAP3 Repository - Tools registration'
    )
