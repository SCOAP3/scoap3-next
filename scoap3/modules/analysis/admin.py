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
from flask import current_app, make_response, request, flash
from flask_admin import BaseView, expose
from flask_admin.contrib.sqla import ModelView
from functools import reduce
from invenio_db import db
from werkzeug.local import LocalProxy

from .models import ArticlesImpact, Gdp


_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


class GdpView(ModelView):
    """View for managing GDP values used in country share calculation."""
    can_view_details = True
    can_edit = True

    column_list = ('id', 'name', 'value1', 'value2', 'value3', 'value4')

    column_default_sort = ('id', True)

    column_labels = {
        'name': "County",
    }

    column_filters = column_list


class ArticleImpactView(ModelView):
    """View for displaying share calculation per article."""
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


class GdpImport(BaseView):
    def parse_data(self, data):
        chars_to_strip = '\r\n ,\'"'
        separator = ';'

        if not data:
            return []

        result = {}
        failed = False

        for row in data.split('\n'):
            row_data = row.split(separator)

            data_count = len(row_data)
            if data_count < 2 or data_count > 5:
                flash('Invalid  data: "%s"' % row, 'warning')
                failed = True

            country = row_data[0].strip(chars_to_strip)
            if country in result:
                flash('Multiple rows found with country "%s". Overriding previous value.' %
                      country, 'warning')

            try:
                values = map(lambda d: float(d), row_data[1:])
                # add dummy values for easier indexing
                values.extend([0] * (4 - len(values)))
                result[country] = values
            except ValueError as _:
                flash('Invalid  data: "%s"' % row, 'warning')
                failed = True

        if failed:
            return []
        return result

    def upload(self, data):
        data = dict(data)  # copy the data, because we will delete the elements

        for gdp in Gdp.query.all():
            if gdp.name in data:
                new_gdp = data[gdp.name]
                gdp.value1 = new_gdp[0]
                gdp.value2 = new_gdp[1]
                gdp.value3 = new_gdp[2]
                gdp.value4 = new_gdp[3]
                del data[gdp.name]

        for k, v in data.iteritems():
            gdp = Gdp()
            gdp.name = k
            gdp.value1 = v[0]
            gdp.value2 = v[1]
            gdp.value3 = v[2]
            gdp.value4 = v[3]
            db.session.add(gdp)

        db.session.commit()
        flash('All done!')

    def test(self, data):
        data = dict(data)  # copy the data, because we will delete the elements
        result = {
            'only_in_db': [],
            'both_places': []
        }

        for gdp in Gdp.query.all():
            if gdp.name in data:
                result['both_places'].append(gdp.name)
                del data[gdp.name]
            else:
                result['only_in_db'].append(gdp.name)

        result['only_in_data'] = data.keys()

        return result

    @expose('/', methods=('GET', 'POST'))
    def index(self):
        raw_data = request.form.get('data', '')
        context = {
            'raw_data': raw_data
        }

        parsed_data = self.parse_data(raw_data)

        if parsed_data:
            if 'upload' in request.form:
                self.upload(parsed_data)
            else:
                context['test_results'] = self.test(parsed_data)

        return self.render('scoap3_analysis/admin/import.html', **context)


class CountriesShare(BaseView):
    """View for displaying country share calculations."""
    @expose('/', methods=('GET', 'POST'))
    def index(self):
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
        message = ""
        if request.method == 'POST':
            if 'run' in request.form:
                celery = Celery()
                celery.conf.update(celery_config_dict)
                celery.send_task(
                    'scoap3.modules.analysis.tasks.calculate_articles_impact',
                    kwargs={'from_date': request.form['from_date'],
                            'until_date': request.form['until_date'],
                            'countries_ordering': request.form['gdp-value'],
                            'step': 50}
                )
                message = "New calculation scheduled."
            elif 'generate_csv' in request.form:
                countries = Gdp.query.order_by(Gdp.name.asc()).all()
                records = ArticlesImpact.query.all()

                header = ['doi', 'recid']
                header.extend([c.name.strip() for c in countries])
                si = StringIO.StringIO()
                cw = csv.writer(si, delimiter=";")
                cw.writerow(header)

                for record in records:
                    total_authors = reduce(lambda x, y: x + y,
                                           record.results.values(), 0)
                    country_share = [float(record.results[c.name.strip()]) / total_authors
                                     if c.name.strip() in record.results else 0
                                     for c in countries]
                    csv_line = [record.doi, record.control_number]
                    csv_line.extend(country_share)
                    cw.writerow(csv_line)

                output = make_response(si.getvalue())
                output.headers["Content-Disposition"] = "attachment; filename=countries_share.csv"
                output.headers["Content-type"] = "text/csv"
                return output

        return self.render('scoap3_analysis/admin/countries_share.html', message=message)


gdp_adminview = {
    'model': Gdp,
    'modelview': GdpView,
    'category': 'Analysis',
    'name': 'GDP list',
}

gdpimport_adminview = {
    'view_class': GdpImport,
    'category': 'Analysis',
    'kwargs': {'category': 'Analysis', 'name': 'GDP import'},
}

articleimpact_adminview = {
    'model': ArticlesImpact,
    'modelview': ArticleImpactView,
    'category': 'Analysis',
}

countriesshare_view = {
    'view_class': CountriesShare,
    'category': 'Analysis',
    'kwargs': {'category': 'Analysis', 'name': 'Countries Share'},
}

__all__ = (
    'gdp_adminview',
    'gdpimport_adminview',
    'articleimpact_adminview',
    'countriesshare_view'
)
