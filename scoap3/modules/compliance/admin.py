# -*- coding: utf-8 -*-
#
# This file is part of SCOAP3 Repository.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Admin views for managing Partner registrations."""

from flask import flash, url_for
from flask_admin.actions import action
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.filters import FilterLike, FilterEqual
from flask_admin.model.template import macro
from invenio_db import db

from .models import Compliance


class FilterByAccepance(FilterEqual):
    def apply(self, query, value, alias=None):
        return query.filter(Compliance.accepted.astext == value)

    def get_options(self, view):
        return (True, 'True'), (False, 'False')


def export_generate_problems(v, c, m, p):
    """Helper function to export 'results' field.
    Filters for not accepted checks, returns the concatenated details.
    """
    problems = [', '.join(r['details']).replace('\n', '')
                for r in m.results['checks'].values() if not r['check']]
    return "\r\n".join(problems)


class ComplianceView(ModelView):
    """View for managing Compliance results."""

    can_edit = False
    can_export = True
    can_delete = False
    can_create = False
    can_view_details = True
    column_default_sort = ('updated', True)

    column_list = ('publisher', 'journal', 'updated', 'recid', 'doi', 'arxiv', 'accepted', 'results', 'history_count')
    column_formatters = {
        'results': macro('render_results'),
        'doi': macro('render_doi'),
        'arxiv': macro('render_arxiv'),
        'accepted': macro('render_accepted'),
        'recid': macro('render_url'),
    }
    column_labels = {
        'results': 'Problems',
        'arxiv': 'arXiv number',
    }
    column_sortable_list = (
        Compliance.updated,
        Compliance.publisher,
        Compliance.journal,
        Compliance.doi,
        Compliance.arxiv,
    )
    column_filters = (
        Compliance.created,
        Compliance.updated,
        FilterByAccepance(column=None, name='Acceptance'),
        FilterLike(column=Compliance.publisher, name='Publisher'),
        FilterLike(column=Compliance.journal, name='Journal'),
        FilterEqual(column=Compliance.doi, name='DOI'),
        FilterEqual(column=Compliance.arxiv, name='arXiv'),
    )

    column_export_list = ('updated', 'publisher', 'journal', 'doi', 'arxiv', 'accepted', 'problems', 'url')
    column_formatters_export = {
        'doi': lambda v, c, m, p: m.doi,
        'arxiv': lambda v, c, m, p: m.arxiv,
        'accepted': lambda v, c, m, p: 'YES' if m.accepted else 'NO',
        'url': lambda v, c, m, p: url_for('compliance.details_view', id='%s,%s' % (m.id, m.id_record), _external=True),
        'problems': export_generate_problems,
    }

    list_template = 'scoap3_compliance/admin/list.html'
    details_template = 'scoap3_compliance/admin/details.html'

    def action_base(self, ids, action):
        """Calls given function for all id separately.
        @:return count of successful actions
        """
        count = 0
        for id in ids:
            id, _ = id.split(',')
            if action(id):
                count += 1

        db.session.commit()
        return count

    @action('accept', 'Accept', 'Are you sure you want to mark all selected record as accepted?')
    def action_accept(self, ids):
        count = self.action_base(ids, Compliance.accept)
        if count > 0:
            flash('%d compliance record(s) were successfully accepted.' % count, 'success')

    @action('reject', 'Reject', 'Are you sure you want to mark all selected record as rejected?')
    def action_reject(self, ids):
        count = self.action_base(ids, Compliance.reject)
        if count > 0:
            flash('%d compliance record(s) were successfully rejected.' % count, 'success')

    @action('rerun', 'Rerun', 'Are you sure you want to run again the compliance check for selected records?')
    def action_rerun(self, ids):
        self.action_base(ids, Compliance.rerun)
        flash('%d record(s) will be checked shortly for compliance. '
              'This process can take a few minutes to complete.' % len(ids), 'success')


compliance_adminview = {
    'model': Compliance,
    'modelview': ComplianceView,
    'category': 'Records',
}

__all__ = (
    'compliance_adminview',
)
