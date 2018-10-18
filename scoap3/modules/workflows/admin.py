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

from flask_admin import expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.filters import FilterEqual
from flask_admin.model.template import macro
from invenio_db import db
from invenio_workflows.models import WorkflowObjectModel, ObjectStatus
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
            json.dumps(m.data, indent=2, sort_keys=True)))
    }
    column_auto_select_related = True
    column_details_list = column_list + ('data', )
    column_details_exclude_list = ('info', )

    list_template = 'scoap3_workflows/admin/list.html'


class WorkflowsOverview(BaseView):
    def get_context_data(self):
        query = db.session\
            .query(WorkflowObjectModel.status, func.count(WorkflowObjectModel.status))\
            .group_by(WorkflowObjectModel.status)

        now = datetime.now()
        last24h = now - timedelta(hours=24)
        last1w = now - timedelta(weeks=1)

        data_last1w = query.filter(WorkflowObjectModel.created >= last1w).all()
        data_last24h = query.filter(WorkflowObjectModel.created >= last24h).all()

        return {
            'last1w': data_last1w,
            'last24h': data_last24h
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
