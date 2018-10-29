# -*- coding: utf-8 -*-
#
# This file is part of SCOAP3 Repository.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Admin views for managing API registrations."""

import csv
import os
import StringIO

from celery import Celery
from flask import current_app, make_response, request
from flask_admin import BaseView, expose
from flask_admin.contrib.sqla import ModelView
from werkzeug.local import LocalProxy

from .models import ArticlesImpact, Gdp


_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)

celery_config_dict = dict(
    BROKER_URL=current_app.config.get(
        "BROKER_URL", ""),
    CELERY_RESULT_BACKEND=current_app.config.get(
        "CELERY_RESULT_BACKEND", ''),
    CELERY_ACCEPT_CONTENT=current_app.config.get(
        "CELERY_ACCEPT_CONTENT", ['json']),
    CELERY_TIMEZONE=current_app.config.get(
        "CELERY_TIMEZONE", 'Europe/Amsterdam'),
    CELERY_DISABLE_RATE_LIMITS=True,
    CELERY_TASK_SERIALIZER='json',
    CELERY_RESULT_SERIALIZER='json',
)


class GdpView(ModelView):
    """View for managing access to API registration."""
    can_view_details = True
    can_edit = True

    column_list = ('id', 'name', 'value1', 'value2', 'value3', 'value4')

    column_default_sort = ('id', True)

    column_labels = {
        'name': "County",
    }

    column_filters = column_list


class ArticleImpactView(ModelView):
    """View for displaying country share calculations."""
    can_view_details = True
    can_edit = True

    column_list = (
        'control_number',
        'created',
        'updated',
        'details',
        'results')

    column_default_sort = ('control_number', True)

    column_labels = {
        'control_number': "recid",
    }

    column_filters = (
        'control_number',
        'created',
        'updated')


class CountriesShare(BaseView):
    @expose('/', methods=('GET', 'POST'))
    def index(self):
        if request.method == 'POST':
            if 'run' in request.form:
                celery = Celery()
                celery.conf.update(celery_config_dict)
                celery.send_task(
                    'scoap3.modules.analysis.tasks.calculate_articles_impact',
                    kwargs={'from_date'=request.form['from_date'],
                            'until_date'=request.form['until_date'],
                            'countries_ordering'=request.form['gdp-value'],
                            'step'=50}
                )
            elif 'generate_csv':
                countries = Gdp.query.order_by(Gdp.name.asc()).all()
                records = ArticlesImpact.query.all()

                csv = ['recid'].extend([c.name.strip() for c in countries])
                si = StringIO.StringIO()
                cw = csv.writer(si, delimiter=";")
                cw.writerows(csv)

                for record in records:
                    total_authors = reduce(lambda x, y: x + y,
                                           record.results.values(), 0)
                    country_share = [float(b[0].results[c.name.strip()]) / total_authors
                                     if c.name.strip() in b[0].results else 0
                                     for c in a]
                    csv_line = [record.control_number].extend(country_share)
                    cw.writerows(csv_line)

                output = make_response(si.getvalue())
                output.headers["Content-Disposition"] = "attachment; filename=countries_share.csv"
                output.headers["Content-type"] = "text/csv"
                return output

        return self.render('scoap3_analysis/admin/countries_share.html', **self.get_context_data())


gdp_adminview = {
    'model': Gdp,
    'modelview': GdpView,
    'kwargs': {'category': 'Analysis', 'name': 'GDP list'},
}

articleimpact_adminview = {
    'model': ArticlesImpact,
    'modelview': ArticleImpactView,
    'category': 'Analysis',
}

countriesshare_view = {
    'category': 'Analysis',
    'view_class': CountriesShare,
    'kwargs': {'category': 'Analysis', 'name': 'Countries Share'},
}

__all__ = (
    'gdp_adminview',
    'articleimpact_adminview',
    'countriesshare_view'
)
