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
from invenio_workflows import restart, resume
from invenio_workflows.models import WorkflowObjectModel, ObjectStatus, Workflow
from markupsafe import Markup
from sqlalchemy import func
from workflow.engine_db import WorkflowStatus


class FilterStatus(FilterEqual):
    def apply(self, query, value, alias=None):
        return query.filter(WorkflowObjectModel.status == int(value))

    def get_options(self, view):
        return [(k, v) for k, v in ObjectStatus.labels.iteritems()]


def data_formatter(v, c, m, p):
    data = '\n'.join([json.dumps(obj.data, indent=2, sort_keys=True) for obj in m.objects])
    return Markup("<pre>%s</pre>" % data)


def error_msg_formatter(v, c, m, p):
    data = '\n'.join([obj.extra_data.get('_error_msg', '') for obj in m.objects])
    return Markup("<pre>%s</pre>" % data)


def msg_formatter(v, c, m, p):
    data = '\n'.join([obj.extra_data.get('_message', '') for obj in m.objects])
    return Markup("<pre>%s</pre>" % data)


class WorkflowView(ModelView):
    """View for managing Compliance results."""

    can_edit = False
    can_delete = False
    can_create = False
    can_view_details = True
    column_default_sort = ('created', True)

    column_list = ('created', 'modified', 'status', 'name', 'info')
    column_labels = {'workflow.name': 'Workflow name'}
    column_sortable_list = ()
    column_filters = (
        'created',
        'modified',
        'name',
        FilterStatus(column=Workflow.status, name='Status')
    )
    column_formatters = {
        'info': macro('render_info'),
        'data': data_formatter,
        'error_msg': error_msg_formatter,
        'message': msg_formatter,
    }
    column_auto_select_related = True
    column_details_list = column_list + ('message', 'error_msg', 'data', )
    column_details_exclude_list = ('info', )

    @action('resume', 'Resume', 'Are you sure?')
    def action_resume(self, ids):
        objects = Workflow.query.filter(Workflow.uuid.in_(ids)).all()

        if len(objects) != len(ids):
            raise ValueError("Invalid id for workflow(s).")

        try:
            for workflow in objects:
                for workflow_object in workflow.objects:
                    resume.apply_async((workflow_object.id,))

            flash("Selected workflow(s) resumed.", "success")
        except Exception as e:
            flash("Failed to resume all selected workflows. Reason: %s" % e.message, "error")

    @action('restart', 'Restart', 'Are you sure?')
    def action_restart(self, ids):
        try:
            for id in ids:
                restart.apply_async((id,))

            flash("Selected workflow(s) restarted.", "success")
        except Exception as e:
            flash("Failed to restart all selected workflows. Reason: %s" % e.message, "error")

    list_template = 'scoap3_workflows/admin/list.html'


class WorkflowsOverview(BaseView):
    def _get_date_from(self):
        last_n_hour = 24
        last_n_days = 0
        try:
            last_n_hour = int(request.args.get('hour_delta', last_n_hour))
            last_n_days = int(request.args.get('day_delta', last_n_days))
        except ValueError:
            flash('Failed to convert time filters, falling back to default.', 'warning')

        return datetime.now() - timedelta(hours=last_n_hour, days=last_n_days)

    def get_context_data(self):
        date_from = self._get_date_from()

        by_status = db.session\
            .query(Workflow.status, func.count(Workflow.status))\
            .group_by(Workflow.status)\
            .filter(Workflow.created >= date_from).all()
        by_status = map(lambda x: (x[0].name, x[1]), by_status)

        by_name = db.session \
            .query(Workflow.name, func.count(Workflow.name)) \
            .group_by(Workflow.name) \
            .filter(Workflow.created >= date_from).all()

        return {
            'by_status': by_status,
            'by_name': by_name,
            'date_from': date_from
        }

    @expose('/', methods=('GET', ))
    def index(self):
        return self.render('scoap3_workflows/admin/overview.html', **self.get_context_data())

    @expose('/', methods=('POST', ))
    def index_post(self):
        date_from = self._get_date_from()

        for w in db.session.query(Workflow.uuid)\
                .filter(Workflow.created >= date_from).filter(Workflow.status == WorkflowStatus.ERROR).all():
            restart.apply_async((str(w.uuid),))

        flash("Restarted workflows in ERROR state that were modified after %s. "
              "Please wait for the tasks to finish." % date_from, 'success')

        return self.index()


workflows = {
    'model': Workflow,
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
