"""Theme blueprint in order for template and static files to be loaded."""

from __future__ import absolute_import, print_function

import logging
from datetime import datetime

from flask import Blueprint, request, jsonify

from werkzeug.utils import secure_filename

from scoap3.modules.records.util import create_from_json
from scoap3.modules.robotupload.config import ROBOTUPLOAD_ALLOWED_USERS, ROBOTUPLOAD_ALLOWED_EXTENSIONS
from scoap3.modules.robotupload.util import save_package, parse_received_package
from .errorhandler import InvalidUsage

logger = logging.getLogger(__name__)

blueprint = Blueprint(
    'scoap3_robotupload',
    __name__,
    url_prefix='/batchuploader',
    template_folder='templates',
    static_folder='static',
)

API_ENDPOINT_DEFAULT = "scoap3.modules.robotupload.tasks.submit_results"


@blueprint.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ROBOTUPLOAD_ALLOWED_EXTENSIONS


def _validate_request():
    """Check if the request comes from a trusted source and parameters are valid."""
    remote_addr = request.environ['REMOTE_ADDR']
    if remote_addr not in ROBOTUPLOAD_ALLOWED_USERS:
        logger.warning('Robotupload access from unauthorized ip address: %s' % remote_addr)
        raise InvalidUsage("Client IP %s cannot use the service." % remote_addr, status_code=403)

    if 'file' not in request.files:
        logger.warning('Robotupload accessed without a file specified. Remote addr: %s' % remote_addr)
        raise InvalidUsage("Please specify file body to input.")

    file = request.files['file']
    if file.filename == '':
        logger.warning('Robotupload accessed without a filename specified. Remote addr: %s' % remote_addr)
        raise InvalidUsage("Please specify file body to input. Filename missing.")

    if not file or not allowed_file(file.filename):
        logger.warning('Robotupload accessed invalid extension: %s. Remote addr: %s' % (file.filename, remote_addr))
        raise InvalidUsage("File does not have an accepted file format.", status_code=415)


def _check_permission_for_journal(journal_title, remote_addr, package_name):
    # check if the user has the right to upload an article with the provided journal title
    allowed_journals_for_user = ROBOTUPLOAD_ALLOWED_USERS.get(remote_addr, ())
    if journal_title not in allowed_journals_for_user and 'ALL' not in allowed_journals_for_user:
        logger.warning('Wrong journal name in metadata for package: %s. Remote addr: %s' % (package_name, remote_addr))
        raise InvalidUsage("Cannot submit such a file from this IP. (Wrong journal)")


def handle_upload_request(apply_async=True):
    """Handle articles that are pushed from publishers."""
    _validate_request()

    remote_addr = request.environ['REMOTE_ADDR']
    file = request.files['file']
    filename = secure_filename(file.filename)
    file_data = file.read()

    logger.info('Package delivered with name %s from %s.' % (filename, remote_addr))

    # save delivered package
    delivery_time = datetime.now().isoformat()
    package_name = '_'.join((delivery_time, filename, remote_addr))
    save_package(package_name, file_data)

    obj = parse_received_package(file_data, package_name)

    journal_title = obj['publication_info'][0]['journal_title']
    _check_permission_for_journal(journal_title, remote_addr, package_name)

    return create_from_json({'records': [obj]}, apply_async=apply_async)


@blueprint.route('/robotupload', methods=['POST', 'PUT'])
def robotupload():
    handle_upload_request()
    return "OK"
