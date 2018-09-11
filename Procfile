# -*- coding: utf-8 -*-
#
# This file is part of SCOAP3.
# Copyright (C) 2014-2018 CERN.
#
# INSPIRE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INSPIRE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with INSPIRE. If not, see <http://www.gnu.org/licenses/>.
#
# In applying this license, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

web: gunicorn scoap3.wsgi # -c gunicorn.cfg
cache: redis-server
worker: celery worker -E -A scoap3.celery --loglevel=INFO --workdir="${VIRTUAL_ENV}" --pidfile="${VIRTUAL_ENV}/worker.pid" -Q celery,harvests
workermon: celery flower -A scoap3.celery
# beat: celery beat -A inspirehep.celery --loglevel=INFO --workdir="${VIRTUAL_ENV}" --pidfile="${VIRTUAL_ENV}/worker_beat.pid"
# mathoid: node_modules/mathoid/server.js -c mathoid.config.yaml
indexer: elasticsearch -Dcluster.name="scoap3" -Ddiscovery.zen.ping.multicast.enabled=false -Dpath.data="$VIRTUAL_ENV/var/data/elasticsearch"  -Dpath.logs="$VIRTUAL_ENV/var/log/elasticsearch"