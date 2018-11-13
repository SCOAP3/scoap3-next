import itertools
import regex
from datetime import timedelta, datetime
from dateutil.parser import parse as parse_date

import requests
from flask import current_app
from invenio_db import db
from invenio_files_rest.models import ObjectVersion
from invenio_mail.api import TemplatedMessage
from invenio_pidstore.models import PersistentIdentifier
from invenio_records import Record
from pdfminer.pdfparser import PDFSyntaxError

from scoap3.modules.compliance.models import Compliance
from scoap3.utils.pdf import extract_text_from_pdf
from scoap3.utils.record import (get_abbreviated_publisher, get_abbreviated_journal, get_arxiv_primary_category,
                                 get_first_doi, get_first_arxiv)


def __extract_article_text(record):
    # fixme extraction shouldn't happen in article_upload?

    extracted_text = {}

    for file in record.get('_files', ()):
        filetype = file['filetype']
        if filetype in ('pdf', 'pdf/a'):
            path = ObjectVersion.get(file['bucket'], file['key']).file.uri
            try:
                extracted_text[filetype] = extract_text_from_pdf(path).decode('utf-8')
            except PDFSyntaxError as e:
                current_app.logger.error('Error while extracting text from pdf with uri %s: %s' % (path, e))

    return extracted_text


def __find_regexp(data, patterns):
    """Finds all matches for given patterns.
    :return list of all matches.
    """

    matches = []

    for original_pattern in patterns:
        # add fuzzing based on pattern length
        fuzz_i = max(len(original_pattern) / 11, 3)

        # add the surrounding characters too
        pattern = "(.{0,10}%s.{0,10}){i<=%d}" % (original_pattern, fuzz_i)

        match = regex.findall(pattern, data, regex.IGNORECASE | regex.DOTALL)
        for m in match:
            # it can contain a string or tuple of strings if there is multiple match groups
            if isinstance(m, tuple):
                matches.append(m[0])
            else:
                matches.append(m)

    return matches


def __find_regexp_in_pdf(extra_data, patterns, forbidden_patterns=None, accept_even_if_not_found=False):
    """
    Finds all matches for given patterns with surrounding characters in all filetypes.
    Fails only if there are no matches at all or there is a match for a forbidden pattern.
    :param patterns: iterable of string patterns
    :param accept_even_if_not_found: check will be accepted if no forbidden patterns are
    found, even if normal patterns are not found.
    """
    check_accepted = True
    details = []

    for filetype, data in extra_data['extracted_text'].iteritems():
        # first check for forbidden patterns
        if forbidden_patterns:
            forbidden_matches = __find_regexp(data, forbidden_patterns)
            if forbidden_matches:
                check_accepted = False
                details.append('Found forbidden match in %s: "%s"' % (filetype, '", "'.join(set(forbidden_matches))))

        matches = __find_regexp(data, patterns)
        if not matches:
            if not accept_even_if_not_found:
                check_accepted = False
            details.append('Not found in %s' % filetype)
        else:
            details.append('Found in %s as: "%s"' % (filetype, '", "'.join(set(matches))))

    return check_accepted, details, None


def _files(record, extra_data):
    """Check if it has the necessary files: .xml, .pdf, .pdfa """

    file_types = [file['filetype'] for file in record.get('_files', ())]

    check_accepted = True
    details = ''

    if 'xml' not in file_types:
        check_accepted = False
        details += 'No xml file. '

    if 'pdf' not in file_types and 'pdf/a' not in file_types:
        check_accepted = False
        details += 'No pdf file. '

    details += 'Available files: %s' % ', '.join(file_types)

    return check_accepted, (details, ), None


def _received_in_time(record, extra_data):
    """Check if publication is not older than 24h """
    api_url = current_app.config.get('CROSSREF_API_URL')

    api_response = requests.get(api_url % get_first_doi(record))
    if api_response.status_code != 200:
        return True, ('Article is not on crossref.', ), 'Api response: %s' % api_response.text

    api_message = api_response.json()['message']

    if 'publication_info' in record and record['publication_info'][0]['journal_title'] == 'Progress of Theoretical and Experimental Physics':
        parts = api_message['published-online']['date-parts'][0]
        # only contains day of publication, check for end of day
        api_time = datetime(*parts, hour=23, minute=59, second=59)
    else:
        api_time = parse_date(api_message['created']['date-time'], ignoretz=True)
    received_time = parse_date(record['record_creation_date'])
    delta = received_time - api_time

    check_accepted = delta <= timedelta(hours=24)
    details_message = 'Arrived %d hours later then creation date on crossref.org.' % (delta.total_seconds() / 3600)
    debug = 'Time from crossref: %s, Received time: %s' % (api_time, received_time)

    return check_accepted, (details_message, ), debug


def _funded_by(record, extra_data):
    """Check if publication has "Funded by SCOAP3" marking *in pdf(a) file* """

    patterns = ['funded.?by.?scoap3?', ]
    return __find_regexp_in_pdf(extra_data, patterns)


def _author_rights(record, extra_data):
    COPYRIGHT = u'\N{COPYRIGHT SIGN}'

    start_patterns = (COPYRIGHT, 'copyright', '\(c\)', )

    needed_patterns = [p + '.{15}' for p in start_patterns]

    forbidden_patterns = ['(iop|institute of physics|elsevier|hindawi|cas|chinese academy of science|'
                          'sissa|dpg|deutsche physikalische gesellschaft|uj|jagiellonian university|oup|'
                          'oxford university press|jps|physical society of japan|springer|sif|'
                          'societa italiana di fisica)', ]

    forbidden_patterns = ['.{0, 10}'.join(x) for x in itertools.product(start_patterns, forbidden_patterns)]

    return __find_regexp_in_pdf(extra_data, needed_patterns, forbidden_patterns, accept_even_if_not_found=True)


def _cc_licence(record, extra_data):
    """Check if publication has appropriate license stated *in pdf(a) file* """
    patterns = ['cc.?by', 'creative.?commons.?attribution', ]
    forbidden_patterns = [
        'cc.?by.?sa', 'creative.?commons.?share.?alike',
        'cc.?by.?nc', 'creative.?commons.?non.?commercial',
        'cc.?by.?nd', 'creative.?commons.?non.?derivatives',
    ]
    return __find_regexp_in_pdf(extra_data, patterns, forbidden_patterns)


def _arxiv(record, extra_data):
    primary = get_arxiv_primary_category(record)
    check_accepted = primary is None or (primary in current_app.config.get('ARXIV_HEP_CATEGORIES'))
    return check_accepted, ('Primary category: %s' % primary, ), None


COMPLIANCE_TASKS = [
    ('Files', _files),
    ('Received in time', _received_in_time),
    ('Funded by', _funded_by),
    ('Author rights', _author_rights),
    ('Licence', _cc_licence),
    ('arXiv', _arxiv),
]


def check_compliance(obj, *args):
    if 'control_number' not in obj.data:
        raise ValueError("Object should have a 'control_number' key in 'data' dict to be consistent with article upload.")

    recid = obj.data['control_number']
    pid = PersistentIdentifier.get('recid', recid)
    record = Record.get_record(pid.object_uuid)

    checks = {}

    # Add temporary data to evalutaion
    extra_data = {'extracted_text': __extract_article_text(record)}

    all_checks_accepted = True
    for name, func in COMPLIANCE_TASKS:
        check_accepted, details, debug = func(record, extra_data)
        all_checks_accepted = all_checks_accepted and check_accepted
        checks[name] = {
            'check': check_accepted,
            'details': details,
            'debug': debug
        }

    c = Compliance.get_or_create(pid.object_uuid)
    results = {
        'checks': checks,
        'accepted': all_checks_accepted,
        'data': {
            'doi': get_first_doi(record),
            'publisher': get_abbreviated_publisher(record),
            'journal': get_abbreviated_journal(record),
            'arxiv': get_first_arxiv(record)
        }
    }

    c.add_results(results)
    c.id_record = pid.object_uuid

    db.session.add(c)
    db.session.commit()

    # send notification about failed checks
    if not all_checks_accepted:
        msg = TemplatedMessage(
            template_html='scoap3_compliance/admin/failed_email.html',
            subject='SCOAP3 - Compliance check',
            sender=current_app.config.get('MAIL_DEFAULT_SENDER'),
            recipients=current_app.config.get('COMPLIANCE_EMAILS'),
            ctx={'results': results}
        )
        current_app.extensions['mail'].send(msg)
