"""Theme blueprint in order for template and static files to be loaded."""

from __future__ import absolute_import, print_function

from flask import Blueprint, request
import os.path
import os
from werkzeug.utils import secure_filename
from scoap3.dojson.hep.model import hep
from dojson.contrib.marc21.utils import create_record
from flask import url_for
from celery import Celery

blueprint = Blueprint(
    'scoap3_robotupload',
    __name__,
    url_prefix='/batchupload',
    template_folder='templates',
    static_folder='static',
)

UPLOAD_FOLDER = '/tmp/robotupload'
ALLOWED_EXTENSIONS = ['xml']
API_ENDPOINT_DEFAULT = "scoap3.modules.robotupload.tasks.submit_results"

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@blueprint.route('/robotupload', methods=['POST'])
def robotupload():
    if 'file' not in request.files:
        return 'No file attached'
    file = request.files['file']
    if file.filename == '':
        return 'No file attached'
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))

    for key in request.form:
        if key == 'mode':
            mode = request.form[key]
        if key == 'nonce':
            nonce = request.form[key]
        if key == 'callback_url':
            callback_url = request.form[key]

    import json
    import codecs
    with open(os.path.join(UPLOAD_FOLDER, filename)) as newfile:
        obj = hep.do(create_record(newfile.read()))
        obj['$schema'] = url_for('invenio_jsonschemas.get_schema', schema_path="hep.json")
        del obj['self']
        print(json.dumps(obj,ensure_ascii=False))
        json_filename = '.'.join([os.path.splitext(filename)[0], 'jl'])
        json_uri = os.path.join(UPLOAD_FOLDER, json_filename)
        f = codecs.open(json_uri, 'w',"utf-8-sig")
        f.write(json.dumps(obj,ensure_ascii=False))
        f.close()

    celery = Celery()
    celery.conf.update(dict(
        BROKER_URL=os.environ.get("APP_BROKER_URL", "amqp://scoap3:bibbowling@scoap3-mq1.cern.ch:5672/scoap3"),
        CELERY_RESULT_BACKEND=os.environ.get("APP_CELERY_RESULT_BACKEND", 'redis://:mypass@scoap3-cache1.cern.ch:6379/1'),
        CELERY_ACCEPT_CONTENT=os.environ.get("CELERY_ACCEPT_CONTENT",['json']),
        CELERY_TIMEZONE=os.environ.get("CELERY_TIMEZONE", 'Europe/Amsterdam'),
        CELERY_DISABLE_RATE_LIMITS=True,
        CELERY_TASK_SERIALIZER='json',
        CELERY_RESULT_SERIALIZER='json',
    ))
    celery.send_task(
        API_ENDPOINT_DEFAULT,
        errors=[]
    )

    return "OK"
