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
from sqlalchemy_utils import EmailType


class ApiRegistrations(db.Model):
    __tablename__ = 'api_registrations'

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    """Primary key. It allows the other fields to be nullable."""

    creation_date = db.Column(db.DateTime, default=datetime.utcnow)

    partner = db.Column(db.Boolean(name='partner'), nullable=False,
                        default=False, server_default='0')

    name = db.Column(db.String(150), nullable=False)

    email = db.Column(EmailType, index=True, nullable=False, unique=True)

    organization = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(100), nullable=False)

    country = db.Column(db.String(80), nullable=False)

    description = db.Column(db.String(1000), nullable=True)

    accepted = db.Column(db.Integer, default=0, server_default='0')
    """0 - new, 1 - acceped, -1 - denied"""

    @classmethod
    def accept(cls, id):
        registration = cls.query.filter_by(id=id).one()
        registration.accepted = 1
        return True

    @classmethod
    def reject(cls, id):
        registration = cls.query.filter_by(id=id).one()
        registration.accepted = -1
        return True
