from __future__ import absolute_import, print_function

from flask import Blueprint, render_template, request
from .models import ApiRegistrations

import sys
from invenio_db import db


blueprint = Blueprint(
    'scoap3_api',
    __name__,
    url_prefix='/partners',
    template_folder='templates',
    static_folder='static',
)


class EmailRegisterdException(Exception):
    pass


class NameUsedException(Exception):
    pass


@blueprint.route('/')
def index():
    return render_template(
        'scoap3_api/index.html',
        title='SCOAP3 Repository - API'
    )


@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    message = ''
    if request.method == 'POST':
        try:
            new_reg = ApiRegistrations(partner=bool(int(request.form['partner'])),
                                       name=request.form['name'],
                                       email=request.form['email'],
                                       organization=request.form['organization'],
                                       role=request.form['role'],
                                       country=request.form['country'],
                                       description=request.form['description']
                                      )
            db.session.add(new_reg)
            db.session.commit()
            message = ('success', "Registration succesful. We will confirm your registration shortly.")
        except EmailRegisterdException():
            message = ('error', "User with this <b>email</b>: {} is already registered.".format(request.args.get('inputEmail')))
        except NameUsedException():
            message = ('error', "User with this <b>name</b>: {} is already registered".format(request.args.get('inputName')))
        except Exception():
            message = ('error', sys.exc_info()[0])

    return render_template(
        'scoap3_api/register.html',
        title='SCOAP3 Repository - Tools registration',
        message=message,
    )


