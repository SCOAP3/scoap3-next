"""Theme blueprint in order for template and static files to be loaded."""

from __future__ import absolute_import, print_function

from flask import Blueprint, request, jsonify
import os.path
import os
from werkzeug.utils import secure_filename
from scoap3.dojson.hep.model import hep
from dojson.contrib.marc21.utils import create_record
from flask import url_for
from celery import Celery
from .errorhandler import InvalidUsage
from . import config

blueprint = Blueprint(
    'scoap3_robotupload',
    __name__,
    url_prefix='/batchuploader',
    template_folder='templates',
    static_folder='static',
)

UPLOAD_FOLDER = '/tmp/robotupload'
API_ENDPOINT_DEFAULT = "scoap3.modules.robotupload.tasks.submit_results"


@blueprint.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config.ROBOTUPLOAD_ALLOWED_EXTENSIONS

@blueprint.route('/robotupload', methods=['POST'])
def robotupload():
    mode = None
    nonce = None
    callback_url = None

    if request.environ['REMOTE_ADDR'] not in config.ROBOTUPLOAD_ALLOWED_USERS:
        raise InvalidUsage("Sorry, client IP %s cannot use the service." % request.environ['REMOTE_ADDR'], status_code=403)
    if 'file' not in request.files:
        raise InvalidUsage("Please specify file body to input.")
    file = request.files['file']
    if file.filename == '':
        raise InvalidUsage("Please specify file body to input.")
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))
    else:
        raise InvalidUsage("File does not have an accepted file format.", status_code=415)

    for key in request.form:
        if key == 'mode':
            mode = request.form[key]
        if key == 'nonce':
            nonce = request.form[key]
        if key == 'callback_url':
            callback_url = request.form[key]

    if not mode:
        raise InvalidUsage("Please specify upload mode to use.")
    if mode == '-teapot':
        raise InvalidUsage("I'm a teapot.", status_code=418, payload="The resulting entity may be short and stout.")
    if mode not in config.ROBOTUPLOAD_UPLOAD_MODES:
        raise InvalidUsage("Invalid upload mode.")

    import json
    import codecs
    with open(os.path.join(UPLOAD_FOLDER, filename)) as newfile:
        try:
            obj = hep.do(create_record(newfile.read()))
        except:
            raise InvalidUsage("MARCXML is not valid.")
        obj['$schema'] = url_for('invenio_jsonschemas.get_schema', schema_path="hep.json")
        del obj['self']

        # TODO - change this ugly mess
        tmp_allowed_journals = config.ROBOTUPLOAD_ALLOWED_USERS[request.environ['REMOTE_ADDR']]
        if obj['metadata']['publication_info'][0]['journal_title'] not in tmp_allowed_journals or 'ALL' not in tmp_allowed_journals:
            raise InvalidUsage("Cannot submit such a file from this IP. (Wrong journal.)")

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
        kwargs={'results_data':obj}
    )

    return "OK"
