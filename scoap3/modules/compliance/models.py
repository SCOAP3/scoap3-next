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

    @hybrid_property
    def publisher(self):
        return self.results['data']['publisher']

    @hybrid_property
    def arxiv(self):
        return self.results['data']['arxiv']

    @classmethod
    def get_or_create(cls, object_uuid):
        c = Compliance.query.filter(Compliance.id_record==object_uuid).first()
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

    def add_results(self, new_results):
        if self.results == new_results or new_results is None:
            return

        if self.results:
            self.history.append({
                'datetime': datetime.now(),
                'results': self.results
            })

        self.results = new_results