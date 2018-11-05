from flask import Blueprint, render_template, url_for, redirect
from flask_menu import register_menu

blueprint = Blueprint(
    'scoap3_accounts',
    __name__,
    url_prefix='/account',
    template_folder='templates'
)


@blueprint.route('/')
def default():
    return redirect(url_for('scoap3_accounts.home'))


@blueprint.route('/settings/')
def default_setting():
    return redirect(url_for('security.change_password'))


@blueprint.route('/home/')
@register_menu(blueprint, 'general.home', text='<i class="fa fa-home fa-fw"></i> Home', order=-1)
def home():
    return render_template('scoap3_accounts/home.html')
