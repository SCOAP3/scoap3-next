"""Theme blueprint in order for template and static files to be loaded."""

from __future__ import absolute_import, print_function

import logging
from datetime import datetime

from flask import Blueprint, request, jsonify

from scoap3.modules.records.util import create_from_json
from scoap3.modules.robotupload.util import save_package, parse_received_package, can_ip_access, \
    get_allowed_journals_by_ip
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
ALLOWED_METHODS = ['POST', 'PUT']


@blueprint.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


def validate_request(remote_addr):
    """
    Check if the request comes from a trusted source and parameters are valid.
    Raises InvalidUsage if not.
    :param remote_addr: remote ip address
    """

    if not can_ip_access(remote_addr):
        logger.warning('Robotupload access from unauthorized ip remote_addr=%s' % remote_addr)
        raise InvalidUsage("Client IP %s cannot use the service." % remote_addr, status_code=403)

    if not request.data:
        logger.warning('Robotupload accessed without data. remote_addr=%s' % remote_addr)
        raise InvalidUsage("Please specify data to input.")


def check_permission_for_journal(journal_title, remote_addr, package_name):
    """
    Checks if the user has the right to upload an article with the provided journal title.
    Raises InvalidUsage if not.
    :param journal_title: title of the journal according to the delviered data
    :param remote_addr: remote ip address
    :param package_name: delivered package name, for logging purposes
    """

    allowed_journals_for_user = get_allowed_journals_by_ip(remote_addr)
    if journal_title not in allowed_journals_for_user and 'ALL' not in allowed_journals_for_user:
        logger.warning('Wrong journal name in metadata. remote_addr=%s package_name=%s journal_title=%s' % (
            remote_addr, package_name, journal_title))
        raise InvalidUsage("Cannot submit such a file from this IP. (Wrong journal)")


def handle_upload_request(apply_async=True):
    """Handle articles that are pushed from publishers."""
    remote_addr = request.environ['REMOTE_ADDR']

    logger.info('Robotupload request received. remote_addr=%s headers=%s args=%s data=%s' % (
        remote_addr, request.headers, request.args, request.data[:100]))
    validate_request(remote_addr)

    package_name = 'robotupload_%s_%s' % (datetime.now().isoformat(), remote_addr)

    logger.info('Package delivered. package_name=%s' % package_name)

    # save delivered package
    file_data = request.data
    save_package(package_name, file_data)

    obj = parse_received_package(file_data, package_name)

    journal_title = obj['publication_info'][0]['journal_title']
    check_permission_for_journal(journal_title, remote_addr, package_name)

    return create_from_json({'records': [obj]}, apply_async=apply_async)


@blueprint.route('/robotupload/<mode>', methods=ALLOWED_METHODS)
def legacy_robotupload(mode):
    """This view is only kept for being compatible with legacy repository url. As soon as legacy is not running
     parallel, this can be removed.
    :param mode: unused. In the legacy repository it was used to differentiate an insertion, replace, etc.
    """
    return robotupload()


@blueprint.route('/robotupload', methods=ALLOWED_METHODS)
def robotupload():
    """View for handling pushing publishers

    Data is expected to be present in http body.
    Example call using curl:
    `curl -H "Content-Type: application/json" --data @data.xml http://localhost:5000/batchuploader/robotupload`
    """
    handle_upload_request()
    return "OK"
