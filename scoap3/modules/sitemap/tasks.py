# -*- coding: utf-8 -*-
#
# This file is part of SCOAP3.
# Copyright (C) 2018 CERN.
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

"""Sitemap tasks."""

from __future__ import absolute_import

import itertools

from celery import shared_task
from flask import current_app, render_template, url_for


@shared_task(ignore_results=True)
def update_sitemap_cache(urls=None, max_url_count=None):
    """Update the Sitemap cache."""

    max_url_count = max_url_count or current_app.config['SITEMAP_MAX_URL_COUNT']
    sitemap = current_app.extensions['scoap3-sitemap']
    urls = iter(urls or sitemap._generate_all_urls())

    url_scheme = current_app.config['SITEMAP_URL_SCHEME']

    urls_slice = list(itertools.islice(urls, max_url_count))
    page_n = 0
    sitemap.clear_cache()
    while urls_slice:
        page_n += 1
        page = render_template('scoap3_sitemap/sitemap.xml', urlset=filter(None, urls_slice))
        sitemap.set_cache('sitemap:' + str(page_n), page)
        urls_slice = list(itertools.islice(urls, max_url_count))

    urlset = [
        {'loc': url_for('scoap3_sitemap.sitemappage', page=pn, _external=True, _scheme=url_scheme)}
        for pn in range(1, page_n + 1)
    ]

    index_page = render_template('scoap3_sitemap/sitemapindex.xml', urlset=urlset, url_scheme=url_scheme)
    sitemap.set_cache('sitemap:0', index_page)
