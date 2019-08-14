# -*- coding: utf-8 -*-
#
# This file is part of SCOAP3.
# Copyright (C) 2016 CERN.
#
# scoap3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# scoap3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with scoap3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

from __future__ import division

from flask import current_app, Blueprint, flash, request
from flask_login import current_user
from invenio_records_rest.query import default_search_factory
from werkzeug.utils import redirect

from scoap3.modules.search.utils import Scoap3RecordsSearch
from scoap3.modules.tools.tasks import run_tool

blueprint = Blueprint(
    'scoap3_search',
    __name__,
    url_prefix='/search',
    template_folder='templates',
    static_folder='static',
)


@blueprint.route('/ping')
def ping():
    return 'OK'


@blueprint.route('/export')
def export():
    """
    Creates a csv export from the records.

    Filters are created based on the get parameters, which are compatible with the api or the search ui.
    """

    search_index = current_app.config.get('SEARCH_UI_SEARCH_INDEX')

    search = Scoap3RecordsSearch(index=search_index)
    search, _ = default_search_factory(None, search)

    params = {
        'es_dict': search.to_dict(),
        'result_email': current_user.email,
        'tool_name': 'search'
    }
    run_tool.apply_async(kwargs=params)

    flash('Export scheduled. As soon as the results are ready, it will be sent to %s' % params['result_email'],
          'success')

    return redirect(request.referrer)
