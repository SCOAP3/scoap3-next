from __future__ import absolute_import, print_function

from flask import Blueprint, render_template, request
from .model import ApiRegistration


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


def check_registration_parameters(args):
    pass


def save_new_registration():
    pass


def create_new_invenio_user():
    pass


def send_notification_email_to_new_user(uid):
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
            check_registration_parameters(request.args)
            save_new_registration()
            uid = create_new_invenio_user()
            send_notification_email_to_new_user(uid)
            message = ('success', "Registration succesful. We will confirm your registration shortly.")
        except EmailRegisterdException():
            message = ('error', "User with this <b>email</b>: {} is already registered.".format(request.args.get('inputEmail')))
        except NameUsedException():
            message = ('error', "User with this <b>name</b>: {} is already registered".format(request.args.get('inputName')))

    return render_template(
        'scoap3_api/register.html',
        title='SCOAP3 Repository - Tools registration',
        message=message,
    )



