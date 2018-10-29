from flask import Blueprint, render_template
from flask_menu import register_menu

blueprint = Blueprint(
    'scoap3_tools',
    __name__,
    url_prefix='/tools',
    template_folder='templates',
)


@blueprint.route('/test')
@register_menu(blueprint, 'general.tools', text='<i class="fa fa-cog fa-fw"></i> Tools')
def test():
    return render_template('scoap3_tools/test.html')
