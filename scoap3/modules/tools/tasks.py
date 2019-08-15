import csv
import logging
from StringIO import StringIO
from datetime import datetime
from gzip import GzipFile

from celery import shared_task
from flask import current_app
from flask_mail import Attachment
from invenio_mail.api import TemplatedMessage

logger = logging.getLogger(__name__)


def encode_element(element):
    """
    Converts element to utf-8 string.

    None value will be converted to an empty string.
    """
    if element is None:
        return ""

    if isinstance(element, basestring):
        return element.encode('utf-8')

    return element


def to_csv(data):
    """
    Serialize generated tool data to CSV.
    :param data: dictionary representing the data to be serialized.
     'header' key has to contain a list of string, 'data' key has to contain a list of list of string.
    :return: (content_type, data) 2-tuple: corresponding MIME type as string and the serialized value as string.
    """
    if not data or 'header' not in data or 'data' not in data:
        raise ValueError('Invalid parameter to be serialized.')

    result = StringIO()
    cw = csv.writer(result, delimiter=";", quoting=csv.QUOTE_ALL)

    cw.writerow(data['header'])

    for row in data['data']:
        cw.writerow([encode_element(element) for element in row])

    return 'text/csv', result.getvalue()


def send_result(result_data, content_type, recipients, tool_name):
    """
    Sends the result via email to the user who requested it.
    :param result_data: generated data in a serialized form.
    :param content_type: MIME type of the attachment.
    :param recipients: recipients who will receive the email.
    :param tool_name: name of the tool, which will be used in the subject of the email.
    """
    timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    filename = 'scoap3_export_%s_%s.csv' % (tool_name, timestamp)

    # compress data if needed
    compress = current_app.config.get('TOOL_COMPRESS_ATTACHMENT', False)
    if compress:
        compressed_buffer = StringIO()
        gzip_file = GzipFile(fileobj=compressed_buffer, mode="wt")
        gzip_file.write(result_data)
        gzip_file.close()

        result_data = compressed_buffer.getvalue()
        content_type = 'application/gzip'
        filename += '.gz'

    attachment = Attachment(filename=filename, content_type=content_type, data=result_data)

    msg = TemplatedMessage(
        template_html='scoap3_tools/email/result.html',
        subject='SCOAP3 - Export %s result' % tool_name,
        sender=current_app.config.get('MAIL_DEFAULT_SENDER'),
        recipients=recipients,
        attachments=[attachment],
    )
    current_app.extensions['mail'].send(msg)


def send_failed_email(recipients, tool_name, task_id=None):
    """
    Notifies the user about a failed generation.
    :param recipients: recipients who will receive the email.
    :param tool_name: name of the tool, which will be used in the subject of the email.
    :param task_id: celery task id, if available.
    """
    msg = TemplatedMessage(
        template_html='scoap3_tools/email/failed.html',
        subject='SCOAP3 - Export %s result error' % tool_name,
        sender=current_app.config.get('MAIL_DEFAULT_SENDER'),
        recipients=recipients,
        ctx={'task_id': task_id}
    )
    current_app.extensions['mail'].send(msg)


@shared_task(bind=True)
def run_tool(self, result_email, tool_name, serializer_function=to_csv, **kwargs):
    """
    Wrapper for generating result for a tool.

    It generates the result using the tool_function parameter's return value, then sends it via email.
    :param self: bound task type instance.
    :param result_email: email address to send the results to.
    :param tool_name: name of the tool, which is used to determine the generator function.
    :param serializer_function: serializer function
    :param kwargs: additional kwargs passed to the tool_function
    """
    try:
        logger.info('Running tool. tool_name=%s result_email=%s' % (tool_name, result_email))

        tool_function = current_app.config.get('TOOL_FUNCTIONS', {}).get(tool_name)
        if tool_function is None:
            logger.warn('Invalid tool name: %s' % tool_name)
            send_failed_email([result_email], tool_name)
            return

        result = tool_function(**kwargs)
        logger.info('Result calculated. result_data_count=%d tool_name=%s result_email=%s' % (
            len(result['data']), tool_name, result_email))

        content_type, serialized_result = serializer_function(result)
        logger.info('Result serialized, sending email... result_data_count=%d tool_name=%s result_email=%s' % (
            len(result['data']), tool_name, result_email))

        send_result(serialized_result, content_type, [result_email], tool_name)

        logger.info('Result successfully sent. tool_name=%s result_email=%s' % (tool_name, result_email))
    except Exception as e:
        # in case an unexpected error occurs, log the details
        logger.error('Unexpected error occured while running an export tool. '
                     'tool_name=%s result_email=%s expection=%s' % (tool_name, result_email, e.message))

        # and notify the user
        recipients = current_app.config.get('OPERATIONS_EMAILS', []) + [result_email]
        send_failed_email(recipients, tool_name, self.request.id)
        raise
