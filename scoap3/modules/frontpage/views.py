# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""SCOAP3 frontpage UI."""

from __future__ import absolute_import, print_function

from flask import Blueprint, render_template
from invenio_search.api import current_search_client
from invenio_collections.models import Collection

blueprint = Blueprint(
    'scoap3_home',
    __name__,
    template_folder='templates',
    static_folder='static',
)

@blueprint.route('/')
def index():
    """SCOAP3 home page."""

    count = current_search_client.count(index="records-record-v1.0.0")
    collections = Collection.query.filter(Collection.level == 2).all()

    return render_template(
        'scoap3_frontpage/home.html',
        title='SCOAP3 Repository',
        articles_count=count['count'],
        collections=collections
    )
