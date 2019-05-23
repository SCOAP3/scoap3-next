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

"""Theme blueprint in order for template and static files to be loaded."""

from __future__ import absolute_import, print_function

from dateutil.parser import parse
from flask import Blueprint
from jinja2.utils import Markup
import json

blueprint = Blueprint(
    'scoap3_theme',
    __name__,
    url_prefix='',
    template_folder='templates',
    static_folder='static',
)


@blueprint.route('/ping')
def ping():
    return 'OK'


@blueprint.app_template_filter()
def is_list(value):
    """Checks if an object is a list."""
    return isinstance(value, list) or None


@blueprint.app_template_filter()
def format_author_name(name):
    return ' '.join(reversed(name.split(',')))


@blueprint.app_template_filter()
def tri_state_boolean_to_icon(inp):
    template = '<span class="glyphicon glyphicon-%s-sign" aria-hidden="true"></span>'
    classes = {
        0: 'question',
        1: 'ok',
        -1: 'remove',
    }
    return Markup(template % classes.get(inp))


@blueprint.app_template_filter()
def boolean_to_icon(inp):
    template = '<span class="glyphicon glyphicon-%s-sign text-%s" aria-hidden="true"></span>'
    if inp:
        return Markup(template % ('ok', 'success'))

    return Markup(template % ('remove', 'danger'))


@blueprint.app_template_filter()
def to_date(inp):
    return parse(inp)


@blueprint.app_template_filter()
def pretty_json(inp):
    return json.dumps(inp, indent=2)
