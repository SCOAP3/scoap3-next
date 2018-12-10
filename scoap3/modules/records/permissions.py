# -*- coding: utf-8 -*-
#
# This file is part of INSPIRE.
# Copyright (C) 2016 CERN.
#
# INSPIRE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INSPIRE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with INSPIRE. If not, see <http://www.gnu.org/licenses/>.
#
# In applying this licence, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

from __future__ import absolute_import, division, print_function

from flask_security import current_user

from flask_principal import ActionNeed
from invenio_access.permissions import (DynamicPermission,
                                        ParameterizedActionNeed,
                                        Permission)


class PublicBucketPermission(object):
    """Permission for files in public buckets.
    Everyone are allowed to read. Admin can do everything.
    """

    def __init__(self, action):
        """Initialize permission."""
        self.action = action

    def can(self):
        """Check permission."""
        if self.action == 'object-read':
            return True
        else:
            return Permission(ActionNeed('admin-access')).can()


def files_permission_factory(obj, action=None):
    return PublicBucketPermission(action)


def record_read_permission_factory(record=None):
    """Record permission factory."""
    return RecordPermission.create(record=record, action='read')


class RecordPermission(object):
    """Record permission.

    - Read access given if collection not restricted.
    - All other actions are denied for the moment.
    """

    read_actions = ['read']

    def __init__(self, record, func, user):
        """Initialize a file permission object."""
        self.record = record
        self.func = func
        self.user = user or current_user

    def can(self):
        """Determine access."""
        return self.func(self.user, self.record)

    @classmethod
    def create(cls, record, action, user=None):
        """Create a record permission."""
        if action in cls.read_actions:
            return cls(record, has_read_permission, user)
        else:
            return cls(record, deny, user)


def has_read_permission(user, record):
    """Check if user has read access to the record."""
    def _cant_view(collection):
        return not DynamicPermission(
            ParameterizedActionNeed(
                'view-restricted-collection',
                collection)).can()

    user_roles = [r.name for r in current_user.roles]
    if 'superuser' in user_roles:
        return True

    # By default we allow access
    return True

#
# Utility functions
#


def deny(user, record):
    """Deny access."""
    return False
