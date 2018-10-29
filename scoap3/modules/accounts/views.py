from flask import Blueprint, render_template
from flask_menu import register_menu

blueprint = Blueprint(
    'scoap3_accounts',
    __name__,
    url_prefix='/accounts',
    template_folder='templates'
)


@blueprint.route('/')
@register_menu(blueprint, 'general.home', text='<i class="fa fa-home fa-fw"></i> Home', order=-1)
def test():
    return render_template('scoap3_accounts/home.html')
