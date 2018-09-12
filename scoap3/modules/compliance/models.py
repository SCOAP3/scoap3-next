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
from invenio_db import db
from invenio_records.models import RecordMetadata
from sqlalchemy.dialects import postgresql
from sqlalchemy_utils import JSONType, UUIDType


class Compliance(db.Model):
    __tablename__ = 'compliance'

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    """Primary key. It allows the other fields to be nullable."""

    created = db.Column(db.DateTime, default=datetime.utcnow)
    updated = db.Column(db.DateTime, onupdate=datetime.utcnow)

    id_record = db.Column(
        UUIDType,
        db.ForeignKey(RecordMetadata.id),
        primary_key=True
    )

    """Id of the community to which the record is applying."""
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
