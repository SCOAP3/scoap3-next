# -*- coding: utf-8 -*-
#
# This file is part of SCOAP3.
# Copyright (C) 2016 CERN.
#
# SCOAP3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# SCOAP3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SCOAP3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Persistent identifier minters."""

from __future__ import absolute_import, print_function

from .providers import SCOAP3RecordIdProvider


def scoap3_recid_minter(record_uuid, data):
    """Mint record identifiers."""
    args = dict(
        object_type='rec',
        object_uuid=record_uuid,
        pid_type=SCOAP3RecordIdProvider.schema_to_pid_type('hep')
    )
    if 'control_number' in data:
        if type(data['control_number']) is list:
            args['pid_value'] = data['control_number'][0]
        else:
            args['pid_value'] = data['control_number']
    provider = SCOAP3RecordIdProvider.create(**args)
    data['control_number'] = str(provider.pid.pid_value)
    return provider.pid
