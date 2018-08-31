# -*- coding: utf-8 -*-
#
# This file is part of SCOAP3 Repository.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Admin views for managing access to actions."""

from flask import current_app, flash, request
from flask_admin import expose
from flask_admin.actions import action
from flask_admin.contrib.sqla import ModelView
from werkzeug.local import LocalProxy
from wtforms import SelectField

from .models import ApiRegistrations
from invenio_db import db
from invenio_access.proxies import current_access
from gettext import ngettext
from flask_mail import Message
from flask_security.forms import ConfirmRegisterForm
from werkzeug.datastructures import MultiDict
from invenio_accounts.models import Role
from flask_security.utils import hash_password

from invenio_mail.api import TemplatedMessage
import os

_datastore = LocalProxy(lambda: current_app.extensions['security'].datastore)


class ApiRegistrationsView(ModelView):
    """View for managing access to actions by users."""

    can_view_details = True
    can_edit = False

    #list_all = ('id', 'creation_date', 'name', 'partner', 'organization', 'email', 'role', 'country', 'description', 'accepted',)
    column_list = ('id', 'creation_date', 'name', 'partner', 'organization', 'email', 'role', 'country', 'description', 'accepted')

    column_default_sort = ('id', True)

    column_labels = {
         'creation_date': "Registration date",
         'name': "Name",
         'email': "E-mail",
    }

    list_template = 'scoap3_api/custom_list.html'
    column_filters = column_list

    def _create_user_for_api_registration(self, api_user_id):
        api_registration = ApiRegistrations.query.filter_by(id=api_user_id).one()
        password = os.urandom(5).encode('hex')

        kwargs = dict(email=api_registration.email, password=password, active='y')
        form = ConfirmRegisterForm(MultiDict(kwargs), csrf_enabled=False)

        u = None
        r = Role.query.filter_by(id=4).one()

        if form.validate():
            kwargs['password'] = hash_password(kwargs['password'])
            kwargs['active'] = True
            u = _datastore.create_user(**kwargs)

            if _datastore.add_role_to_user(u, r):
                msg = TemplatedMessage(template_html='scoap3_api/email.html',
                                       subject='SCOAP3 - API registration confirmation',
                                       sender='from@example.org',
                                       recipients=[api_registration.email],
                                       ctx={'email': api_registration.email,
                                            'password': password,
                                            'recipient': api_registration.name
                                            })
                current_app.extensions['mail'].send(msg)
        else:
           flash('Error creating user. %s' % form.errors, 'error')

    @action('accept', 'Accept','Are you sure you want to accept selected API registrations?')
    def action_accept(self, ids):
        """Accept users."""
        try:
            count = 0
            for api_user_id in ids:
                user = ApiRegistrations.query.filter_by(id = api_user_id).one()
                if user.accepted == 1:
                    flash('API user %s was already accepted.' % (user.email,), 'warning')
                    continue
                if not ApiRegistrations.accept(api_user_id):
                    raise ValueError("Cannot find API user registration.")
                else:
                    count += 1
                self._create_user_for_api_registration(api_user_id)
            db.session.commit()
            if count > 0:
                flash('API user(s) were successfully accepted.', 'success')
        except Exception as exc:
            if not self.handle_view_exception(exc):
                raise

            current_app.logger.exception(str(exc))  # pragma: no cover
            flash('Failed to accept API users.','error')  # pragma: no cover

    @action('reject', 'Reject','Are you sure you want to reject selected API registrations?')
    def action_reject(self, ids):
        """Accept users."""
        try:
            count = 0
            for api_user_id in ids:
                if not ApiRegistrations.reject(api_user_id):
                    raise ValueError("Cannot find API user registration.")
                else:
                    count += 1
            db.session.commit()
            if count > 0:
                flash('API user(s) were successfully rejected.', 'success')
        except Exception as exc:
            if not self.handle_view_exception(exc):
                raise

            current_app.logger.exception(str(exc))  # pragma: no cover
            flash('Failed to reject API users.','error')  # pragma: no cover


api_registrations_adminview = {
    'model': ApiRegistrations,
    'modelview':ApiRegistrationsView,
    'category': 'Api Registrations',
}

__all__ = (
    'api_registrations_adminview',
)
                                    
