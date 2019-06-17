# -*- coding: utf-8 -*-
#
# This file is part of SCOAP3 Repository.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Database models for access module."""

from __future__ import absolute_import, print_function

from datetime import datetime

from flask import flash
from invenio_db import db
from invenio_records.models import RecordMetadata
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy_utils import UUIDType

from scoap3.modules.workflows.utils import start_compliance_workflow


class Compliance(db.Model):
    __tablename__ = 'compliance'

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    id_record = db.Column(
        UUIDType,
        db.ForeignKey(RecordMetadata.id),
        primary_key=True
    )
    record = db.relationship(RecordMetadata, foreign_keys=[id_record])

    results = db.Column(postgresql.JSONB(none_as_null=True),
                        nullable=False
                        )

    history = db.Column(postgresql.JSONB(none_as_null=True),
                        nullable=False,
                        default=[]
                        )

    @hybrid_property
    def accepted(self):
        return self.results['accepted']

    @hybrid_property
    def doi(self):
        return self.results['data']['doi']

    @doi.expression
    def doi(cls):
        return cls.results['data']['doi'].astext

    @hybrid_property
    def publisher(self):
        return self.results['data']['publisher']

    @publisher.expression
    def publisher(cls):
        return cls.results['data']['publisher'].astext

    @hybrid_property
    def journal(self):
        return self.results['data']['journal']

    @journal.expression
    def journal(cls):
        return cls.results['data']['journal'].astext

    @hybrid_property
    def arxiv(self):
        return self.results['data']['arxiv']

    @arxiv.expression
    def arxiv(cls):
        return cls.results['data']['arxiv'].astext

    @property
    def history_count(self):
        return len(self.history)

    @classmethod
    def get_or_create(cls, object_uuid):
        c = Compliance.query.filter(Compliance.id_record == object_uuid).first()
        return c or cls()

    @classmethod
    def accept(cls, id):
        o = cls.query.filter_by(id=id).one()
        if o.results['accepted']:
            flash('Compliance check with id "%s" was already accepted.' % o.id, 'warning')
            return False

        o.results['accepted'] = True

        # https://bugs.launchpad.net/fuel/+bug/1482658
        # since dict ref. haven't changed need to manually report the change
        flag_modified(o, 'results')

        return True

    @classmethod
    def reject(cls, id):
        o = cls.query.filter_by(id=id).one()
        if not o.results['accepted']:
            flash('Compliance check with id "%s" was already rejected.' % o.id, 'warning')
            return False

        o.results['accepted'] = False

        # https://bugs.launchpad.net/fuel/+bug/1482658
        # since dict ref. haven't changed need to manually report the change
        flag_modified(o, 'results')

        return True

    @classmethod
    def rerun(cls, id):
        """Starts a compliance check for the same record. Previous checks won't be deleted."""
        o = cls.query.filter_by(id=id).one()
        start_compliance_workflow(o.record)

    def add_results(self, new_results):
        if self.results == new_results or new_results is None:
            return

        if self.results:
            self.history.append({
                'created': self.created.isoformat(),
                'results': self.results
            })
            flag_modified(self, 'history')

        self.results = new_results
        flag_modified(self, 'results')

    def has_final_result_changed(self):
        """
        Returns true if there are no history entries or if the last history entry and current result
        have different accepted value.
        """
        return not self.history or self.history[0]['results']['accepted'] != self.results['accepted']
