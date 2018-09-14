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
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy_utils import JSONType, UUIDType


class Compliance(db.Model):
    __tablename__ = 'compliance'

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    updated = db.Column(db.DateTime, onupdate=datetime.utcnow)
    id_record = db.Column(
        UUIDType,
        db.ForeignKey(RecordMetadata.id),
        primary_key=True
    )
    record = db.relationship(RecordMetadata, foreign_keys=[id_record])

    results = db.Column(db.JSON().with_variant(
            postgresql.JSONB(none_as_null=True),
            'postgresql',
        ).with_variant(
            JSONType(),
            'sqlite',
        ).with_variant(
            JSONType(),
            'mysql',
        ),
        default=lambda: dict(),
        nullable=False
    )

    @property
    def accepted(self):
        return self.results.get('accepted', False)

    @property
    def doi(self):
        return self.record.json['dois'][0]['value']

    @property
    def publisher(self):
        return self.record.json['imprints'][0]['publisher']

    @property
    def arxiv(self):
        # todo
        return 'todo'

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
