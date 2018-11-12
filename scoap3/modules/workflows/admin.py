# -*- coding: utf-8 -*-
#
# This file is part of SCOAP3 Repository.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Admin views for managing API registrations."""
import json
from datetime import timedelta, datetime

from flask import flash, request
from flask_admin import expose, BaseView
from flask_admin.actions import action
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.filters import FilterEqual
from flask_admin.model.template import macro
from invenio_db import db
from invenio_workflows import restart
from invenio_workflows.models import WorkflowObjectModel, ObjectStatus, Workflow
from markupsafe import Markup
from sqlalchemy import func


class FilterStatus(FilterEqual):
    def apply(self, query, value, alias=None):
        return query.filter(WorkflowObjectModel.status == int(value))

    def get_options(self, view):
        return [(k, v) for k, v in ObjectStatus.labels.iteritems()]


class WorkflowView(ModelView):
    """View for managing Compliance results."""

    can_edit = False
    can_delete = False
    can_create = False
    can_view_details = True
    column_default_sort = ('created', True)

    column_list = ('created', 'modified', 'status', 'workflow.name', 'info')
    column_labels = {'workflow.name': 'Workflow name'}
    column_sortable_list = ()
    column_filters = (
        'created',
        'modified',
        'workflow.name',
        FilterStatus(column=WorkflowObjectModel.status, name='Status')
    )
    column_formatters = {
        'info': macro('render_info'),
        'data': lambda v, c, m, p: Markup("<pre>{0}</pre>".format(
            json.dumps(m.data, indent=2, sort_keys=True))),
        'error_msg': lambda v, c, m, p: Markup("<pre>{0}</pre>".format(
            m.extra_data.get('_error_msg', ''))),
    }
    column_auto_select_related = True
    column_details_list = column_list + ('error_msg', 'data', )
    column_details_exclude_list = ('info', )

    def action_base(self, ids, action):
        objects = WorkflowObjectModel.query.filter(WorkflowObjectModel.id.in_(ids)).all()

        if len(objects) != len(ids):
            raise ValueError("Invalid id for workflow(s).")

        for workflow in objects:
            action.apply_async((str(workflow.workflow.uuid),))

    @action('restart', 'Restart', 'Are you sure?')
    def action_restart(self, ids):
        try:
            self.action_base(ids, restart)
            flash("Selected workflow(s) restarted.", "success")
        except Exception as e:
            flash("Failed to restart all selected workflows. Reason: %s" % e.message, "error")

    list_template = 'scoap3_workflows/admin/list.html'


class WorkflowsOverview(BaseView):
    def get_context_data(self):
        last_n_hour = 24
        last_n_days = 0
        try:
            last_n_hour = int(request.args.get('hour_delta', last_n_hour))
            last_n_days = int(request.args.get('day_delta', last_n_days))
        except ValueError:
            flash('Failed to convert time filters, falling back to default.', 'warning')

        date_from = datetime.now() - timedelta(hours=last_n_hour, days=last_n_days)

        by_status = db.session\
            .query(WorkflowObjectModel.status, func.count(WorkflowObjectModel.status))\
            .group_by(WorkflowObjectModel.status)\
            .filter(WorkflowObjectModel.created >= date_from).all()
        by_status = map(lambda x: (x[0].name, x[1]), by_status)

        by_name = db.session \
            .query(Workflow.name, func.count(Workflow.name)) \
            .group_by(Workflow.name) \
            .filter(WorkflowObjectModel.created >= date_from).all()

        return {
            'by_status': by_status,
            'by_name': by_name,
            'date_from': date_from
        }

    @expose('/')
    def index(self):
        return self.render('scoap3_workflows/admin/overview.html', **self.get_context_data())


workflows = {
    'model': WorkflowObjectModel,
    'modelview': WorkflowView,
    'category': 'Workflows',
    'name': 'Workflows',
}

workflows_summary = {
    'category': 'Workflows',
    'view_class': WorkflowsOverview,
    'kwargs': {'category': 'Workflows', 'name': 'Summary'},
}

__all__ = (
    'workflows',
    'workflows_summary',
)
