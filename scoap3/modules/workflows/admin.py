# -*- coding: utf-8 -*-
#
# This file is part of SCOAP3 Repository.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Admin views for managing Partner registrations."""
import json
from datetime import timedelta, datetime

from flask import flash, request, url_for
from flask_admin import expose, BaseView
from flask_admin.actions import action
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.filters import FilterEqual
from flask_admin.model.template import macro
from invenio_db import db
from invenio_workflows import restart, resume
from invenio_workflows.models import Workflow
from markupsafe import Markup
from sqlalchemy import func
from workflow.engine_db import WorkflowStatus


class FilterStatus(FilterEqual):
    def apply(self, query, value, alias=None):
        return query.filter(Workflow.status == int(value))

    def get_options(self, view):
        return [(k, v) for k, v in WorkflowStatus.labels.iteritems()]


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

    can_edit = True
    can_delete = True
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

    edit_template = 'scoap3_workflows/admin/workflow_edit.html'
    list_template = 'scoap3_workflows/admin/workflow_list.html'

    def get_save_return_url(self, model, is_created=False):
        return url_for('workflow.edit_view', id=model.uuid)

    def validate_form(self, form):
        """Override base validation as the validation is done at a later step."""
        return True

    def update_model(self, form, model):
        try:
            new_json_data = request.form.get('data')
            if new_json_data:
                new_json = json.loads(new_json_data)
                if len(model.objects) == 1:
                    model.objects[0].data = new_json
                    self.session.commit()
                else:
                    flash('Model has %d objects. Cannot update it as it needs to have exactly one.', 'error')
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash('Failed to update workflow. %s' % str(ex), 'error')

            self.session.rollback()
            return False
        else:
            self.after_model_change(form, model, False)

        return True

    def after_model_change(self, form, model, is_created):
        if 'submit_continue' in request.form:
            self.action_resume((str(model.uuid), ))

        elif 'submit_restart' in request.form:
            self.action_restart((str(model.uuid), ))

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


workflows = {
    'model': Workflow,
    'modelview': WorkflowView,
    'category': 'Workflows',
    'name': 'Edit workflows',
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
