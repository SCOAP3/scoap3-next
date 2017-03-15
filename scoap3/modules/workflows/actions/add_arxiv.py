# -*- coding: utf-8 -*-
#
# This file is part of INSPIRE.
# Copyright (C) 2014, 2015, 2016 CERN.
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
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

"""Approval action for INSPIRE arXiv harvesting."""

from __future__ import absolute_import, division, print_function
from flask import render_template, url_for


class AddArxiv(object):
    """Class representing the add arXiv action."""
    name = "Add arXiv"
    url = url_for("harvesting.resolve_action")

    def render_mini(self, obj):
        """Method to render the minified action."""
        return render_template(
            'workflows/actions/add_arxiv_mini.html',
            message=obj.get_action_message(),
            object=obj,
            resolve_url=self.url,
        )

    def render(self, obj):
        """Method to render the action."""
        return {
            "side": render_template('workflows/actions/add_arxiv_side.html',
                                    message=obj.get_action_message(),
                                    object=obj,
                                    resolve_url=self.url,),
            "main": render_template('workflows/actions/add_arxiv_main.html',
                                    message=obj.get_action_message(),
                                    object=obj,
                                    resolve_url=self.url,)
        }

    def resolve(self, bwo):
        """Resolve the action taken in the approval action."""
        from flask import request
        new_arxiv_id = request.form.get("arxiv_id", None)

        bwo.remove_action()
        data = bwo.get_data()

        if "report_numbers" not in data:
            data["report_numbers"] = []

        data["report_numbers"].append({'source':'arXiv', 'value':new_arxiv_id})
        bwo.set_data(data)
        bwo.save()
        bwo.continue_workflow(start_point="restart_task",delayed=True)
        return {
            "message": "Record has been update!",
            "category": "success",
        }
