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
from sqlalchemy import UniqueConstraint
from sqlalchemy.event import listen
from sqlalchemy.orm import validates


class ApiRegistrations(db.Model):

    __tablename__ = 'api_registrations'

    __table_args__ = (UniqueConstraint(
        'name', 'email',
        name='api_registrations_unique'),
    )

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    """Primary key. It allows the other fields to be nullable."""

    creation_date = db.Column(db.DateTime, default=datetime.utcnow)

    partner = db.Column(db.Boolean(name='partner'), nullable=False,
                        default=False, server_default='0')

    name = db.Column(db.String(150), nullable=False)

    email = db.Column(db.String(100), index=True)

    organization = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(100), nullable=False)

    country = db.Column(db.String(80), nullable=False)

    description = db.Column(db.String(1000), nullable=True)

    accepted = db.Column(db.Integer, default=0, server_default='0')
    """0 - new, 1 - acceped, -1 - denied"""


    @classmethod
    def accept(cls, id):
        registration = cls.query.filter_by(id == id).one()
        registration.accepted = 1
        return True

    @classmethod
    def reject(cls, id):
        registration = cls.query.filter_by(id == id).one()
        registration.accepted = -1
        return True

    # @classmethod
    # def create(cls, action, **kwargs):
    #     """Create new database row using the provided action need.
    #     :param action: An object containing a method equal to ``'action'`` and
    #         a value.
    #     :param argument: The action argument. If this parameter is not passed,
    #         then the ``action.argument`` will be used instead. If the
    #         ``action.argument`` does not exist, ``None`` will be set as
    #         argument for the new action need.
    #     :returns: An :class:`invenio_access.models.ActionNeedMixin` instance.
    #     """
    #     assert action.method == 'action'
    #     argument = kwargs.pop('argument', None) or getattr(
    #         action, 'argument', None)
    #     return cls(
    #         action=action.value,
    #         argument=argument,
    #         **kwargs
    #     )

    # @classmethod
    # def allow(cls, action, **kwargs):
    #     """Allow the given action need.
    #     :param action: The action to allow.
    #     :returns: A :class:`invenio_access.models.ActionNeedMixin` instance.
    #     """
    #     return cls.create(action, exclude=False, **kwargs)

    # @classmethod
    # def deny(cls, action, **kwargs):
    #     Deny the given action need.
    #     :param action: The action to deny.
    #     :returns: A :class:`invenio_access.models.ActionNeedMixin` instance.
        
    #     return cls.create(action, exclude=True, **kwargs)

    # @classmethod
    # def query_by_action(cls, action, argument=None):
    #     """Prepare query object with filtered action.
    #     :param action: The action to deny.
    #     :param argument: The action argument. If it's ``None`` then, if exists,
    #         the ``action.argument`` will be taken. In the worst case will be
    #         set as ``None``. (Default: ``None``)
    #     :returns: A query object.
    #     """
    #     query = cls.query.filter_by(action=action.value)
    #     argument = argument or getattr(action, 'argument', None)
    #     if argument is not None:
    #         query = query.filter(db.or_(
    #             cls.argument == str(argument),
    #             cls.argument.is_(None),
    #         ))
    #     else:
    #         query = query.filter(cls.argument.is_(None))
    #     return query

    # @property
    # def need(self):
    #     """Return the need corresponding to this model instance.
    #     This is an abstract method and will raise NotImplementedError.
    #     """
    #     raise NotImplementedError()  # pragma: no cover
    # """ActionUsers data model.
    # It relates an allowed action with a user.
    # """

    # @property
    # def need(self):
    #     """Return UserNeed instance."""
    #     return UserNeed(self.user_id)
