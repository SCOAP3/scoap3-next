# -*- coding: utf-8 -*-
#
# This file is part of SCOAP3.
# Copyright (C) 2018 CERN.
#
# SCOAP3 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SCOAP3 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SCOAP3. If not, see <http://www.gnu.org/licenses/>.
#
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

import click

from flask.cli import with_appcontext

from scoap3.modules.workflows.utils import start_compliance_workflow
from scoap3.utils.processor import process_all_records


def info(msg):
    click.echo(msg)


def error(msg):
    click.echo(click.style(msg, fg='red'))


@click.group()
def compliance():
    """Compliance commands."""


@compliance.command()
@with_appcontext
@click.option('--ids', default=None,
              help="Comma separated list of recids to be processed or "
                   "'all' if compliance should be checked for all records. eg. '98,324'")
def run(ids):
    """Run compliance check for selected records"""

    if ids == 'all':
        ids_filter = ()
    else:
        ids_filter = ids.split(',')

    process_all_records(start_compliance_workflow, control_ids=ids_filter)

    info('Command finished.')
