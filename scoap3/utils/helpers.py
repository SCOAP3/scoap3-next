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
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

"""Various helpers for the overlay."""

from __future__ import absolute_import, division, print_function

from contextlib import closing
from os.path import basename

import requests


def download_file(url, output_file=None, chunk_size=1024):
    """Download a file to specified location."""
    r = requests.get(
        url=url,
        stream=True
    )
    if r.status_code == 200:
        with open(output_file, 'wb') as f:
            for chunk in r.iter_content(chunk_size):
                f.write(chunk)
    return output_file


def download_file_to_record(record, name, url):
    """Download a file to specified location."""
    with closing(requests.get(url=url, stream=True)) as req:
        if req.status_code == 200:
            record.files[name] = req.raw
            return record.files[name]


def get_json_for_plots(plots):
    """Return proper FFT format from plotextracted plots."""
    output_records = []
    index = 0
    for plot in plots:
        output_records.append(dict(
            url=plot.get('url'),
            docfile_type='Plot',
            description="{0:05d} {1}".format(index, "".join(plot.get('captions', []))),
            filename=plot.get('name'),
        ))
        index += 1
    return dict(fft=output_records)


def force_force_list(data):
    """Wrap data in list.
    We need to define this awkardly named method because DoJSON's method
    force_list returns tuples or None instead of lists.
    """
    if data is None:
        return []
    elif not isinstance(data, (list, tuple, set)):
        return [data]
    elif isinstance(data, (tuple, set)):
        return list(data)
    return data


def clean_oup_package_name(package):
    """
    Returns a clean package name without any path information or postfix. If none of the registered ending is found,
    the basename will be returned.

    Example:
    input:  '/harvest/oup/2019-03-30_16:30:41_ptep_iss_2019_3.img.zip'
    output: '2019-03-30_16:30:41_ptep_iss_2019_3'
    """

    if package is None:
        return ''

    filename = basename(package)
    remove_endings = ('_archival.zip', '.img.zip', '.pdf.zip', '.xml.zip', '.issue.equation_images.zip',
                      '_archival_pdf.zip', '.archival.zip', '.medium_images.zip', '.text_images.zip',
                      '.img_v1.zip', '.pdf_v1.zip', '.xml_v1.zip', '_archival_v1.zip',
                      '.zip')
    for ending in remove_endings:
        if filename.endswith(ending):
            return filename[:-len(ending)]

    return filename
