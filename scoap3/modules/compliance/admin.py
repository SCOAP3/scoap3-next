# -*- coding: utf-8 -*-
#
# This file is part of SCOAP3 Repository.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Admin views for managing API registrations."""

from flask_admin.contrib.sqla import ModelView
from .models import Compliance


class ComplianceView(ModelView):
    """View for managing Compliance results."""

    can_edit = True
    can_delete = False
    column_default_sort = ('id', True)


compliance_adminview = {
    'model': Compliance,
    'modelview': ComplianceView,
    'category': 'Compliance',
}

__all__ = (
    'compliance_adminview',
)
