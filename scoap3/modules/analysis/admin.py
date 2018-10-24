# -*- coding: utf-8 -*-
#
# This file is part of SCOAP3 Repository.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Admin views for managing API registrations."""

from flask import current_app
from flask_admin.contrib.sqla import ModelView
from werkzeug.local import LocalProxy
from .models import Gdp, ArticlesImpact


_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


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


gdp_adminview = {
    'model': Gdp,
    'modelview': GdpView,
    'category': 'Analysis',
}

articleimpact_adminview = {
    'model': ArticlesImpact,
    'modelview': ArticleImpactView,
    'category': 'Analysis',
}

__all__ = (
    'gdp_adminview',
    'articleimpact_adminview'
)
