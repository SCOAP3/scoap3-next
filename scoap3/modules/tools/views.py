from flask import Blueprint, render_template, request, current_app, flash
from flask_login import login_required, current_user
from flask_menu import register_menu

from scoap3.modules.tools.tasks import run_tool

blueprint = Blueprint(
    'scoap3_tools',
    __name__,
    url_prefix='/tools',
    template_folder='templates',
)


def handle_tool_post():
    """Creates an async tool task if there was a valid POST request."""
    if request.method != 'POST':
        return

    tool_functions = current_app.config.get('TOOL_FUNCTIONS', {})
    tool_name = request.form.get('tool_name')

    if tool_name not in tool_functions:
        flash('Invalid selected tool!', 'error')
        return

    params = dict(request.form.items())
    params['result_email'] = current_user.email

    run_tool.apply_async(kwargs=params)
    flash('Export scheduled. As soon as the results are ready, it will be sent to %s' % params['result_email'],
          'success')


@blueprint.route('/', methods=('GET', 'POST'))
@register_menu(blueprint, 'general.tools', text='<i class="fa fa-cog fa-fw"></i> Tools')
@login_required
def tools_main():
    """Interface for scheduling tools."""
    handle_tool_post()
    return render_template('scoap3_tools/main.html')
