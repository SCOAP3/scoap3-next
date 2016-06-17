# -*- coding: utf-8 -*-
#
# This file is part of SCOAP3.
# Copyright (C) 2016 CERN.
#
# SCOAP3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# SCOAP3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SCOAP3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Search blueprint in order for template and static files to be loaded."""

from __future__ import absolute_import, print_function

from flask import Blueprint, current_app, request, render_template

blueprint = Blueprint('scoap3_search',
                      __name__,
                      url_prefix='',
                      template_folder='templates',
                      static_folder='static')


@blueprint.route("/search")
def search():
    """ Main search endpoint.
    Parse the request, perform search and show the results """
    query_params = parse_query_parameters(request.args)

    query_result = es_search(query_params['q'],
                             filters=query_params['filters'],
                             size=query_params['size'],
                             sort_field=query_params['sorting_field'],
                             sort_order=query_params['sorting_order'],
                             offset=query_params['offset'])

    total_pages = calculate_total_pages(query_result, query_params['size'])

    if query_params['current_page'] > total_pages:
        query_params['current_page'] = total_pages

    facets = filter_facets(query_result['facets'], query_result['total'])
    facets = sort_facets(facets)

    year_facet = process_year_facet(request, facets)

    if ('format' in request.args and request.args['format'] == 'json') \
        or 'json' in request.headers['accept']:
        query_result['hits'] = {'total': query_result['total']}
        return jsonify(query_result)
    else:
        ctx = {
            'results': query_result['results'],
            'total_hits': query_result['total'],
            'facets': facets,
            'year_facet': year_facet,
            'q': query_params['q'],
            'max_results': query_params['size'],
            'pages': {'current': query_params['current_page'],
                      'total': total_pages},
            'filters': dict(query_params['filters']),
        }

        if query_params['min_date'] is not sys.maxsize:
            ctx['min_year'] = query_params['min_date']
            ctx['max_year'] = query_params['max_date']

        ctx['modify_query'] = modify_query

        return render_template('search_results.html', ctx=ctx)

