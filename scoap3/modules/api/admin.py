# -*- coding: utf-8 -*-
#
# This file is part of SCOAP3 Repository.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Admin views for managing access to actions."""

from flask import current_app
from flask_admin.contrib.sqla import ModelView
from werkzeug.local import LocalProxy
from wtforms import SelectField

from .models import ApiRegistrations
from .proxies import current_access

_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


def _(x):
    """Identity."""
    return x


class ApiRegistrationsView(ModelView):
    """View for managing access to actions by users."""

    can_view_details = True

    list_all = ('id', 'creation_date', 'name', 'organization', 'email', 'role', 'country', 'description', 'accepted')

    column_list = list_all

    column_default_sort = ('id', True)

    column_labels = {
        'creation_date': _("Registration date"),
        'name': _("Name"),
        'email': _("E-mail"),
    }

    column_filters = list_all

    form_columns = ('accepted')

    # form_args = dict(
    #     action=dict(
    #         choices=LocalProxy(lambda: [
    #             (action, action) for action in current_access.actions.keys()
    #         ])
    #     )
    # )
    # form_overrides = dict(
    #     action=SelectField,
    # )

api_registrations_adminview = {
    'model': ApiRegistrations,
    'modelview': ApiRegistrationsView,
    'category': _('User Management'),
    'name': _('API: registrations')
}
