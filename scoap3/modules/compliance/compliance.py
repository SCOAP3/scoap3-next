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


def __get_first_doi(obj):
    return obj.data['dois'][0]['value']


def __get_first_arxiv(obj):
    arxiv_array = [
        a['value'].split(':')[1]
        for a in obj.data.get('report_numbers', ())
        if a['source'] == 'arXiv'
    ]
    if arxiv_array:
        return arxiv_array[0]
    return None


def __extract_article_text(obj):
    # fixme extraction shouldn't happen in article_upload?

    extracted_text = {}

    for file in obj.data['_files']:
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
        fuzz_i = len(original_pattern) / 11

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


def __find_regexp_in_pdf(extra_data, patterns, forbidden_patterns=None):
    """
    Finds all matches for given patterns with surrounding characters in all filetypes.
    Fails only if there are no matches at all or there is a match for a forbidden pattern.
    :param patterns: iterable of string patterns
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
            check_accepted = False
            details.append('Not found in %s' % filetype)
        else:
            details.append('Found in %s as: "%s"' % (filetype, '", "'.join(set(matches))))

    return check_accepted, details, None


def _files(obj, extra_data):
    """Check if it has the necessary files: .xml, .pdf, .pdfa """

    file_types = [file['filetype'] for file in obj.data['_files']]

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


def _received_in_time(obj, extra_data):
    """Check if publication is not older than 24h """
    api_url = current_app.config.get('CROSSREF_API_URL')

    api_message = requests.get(api_url % __get_first_doi(obj)).json()['message']

    if 'publication_info' in obj.data and obj.data['publication_info'][0]['journal_title'] == 'Progress of Theoretical and Experimental Physics':
        parts = api_message['published-online']['date-parts'][0]
        # only contains day of publication, check for end of day
        api_time = datetime(*parts, hour=23, minute=59, second=59)
    else:
        api_time = parse_date(api_message['created']['date-time'], ignoretz=True)
    received_time = parse_date(obj.data['record_creation_date'])
    delta = received_time - api_time

    check_accepted = delta <= timedelta(hours=24)
    details_message = 'Arrived %d hours later then creation date on crossref.org.' % (delta.total_seconds() / 3600)
    debug = 'Time from crossref: %s, Received time: %s' % (api_time, received_time)

    return check_accepted, (details_message ,), debug


def _funded_by(obj, extra_data):
    """Check if publication has "Funded by SCOAP3" marking *in pdf(a) file* """

    patterns = ['scoap3?', ]
    return __find_regexp_in_pdf(extra_data, patterns)


def _author_rights(obj, extra_data):
    COPYRIGHT = u'\N{COPYRIGHT SIGN}'

    start_patterns = (COPYRIGHT, 'copyright', '\(c\)', )

    needed_patterns = [p + '.{15}' for p in start_patterns]

    forbidden_patterns = ['iop', 'institute of physics', 'elsevier', 'hindawi', 'cas', 'chinese academy of science',
                          'sissa', 'dpg', 'deutsche physikalische gesellschaft', 'uj', 'jagiellonian university', 'oup',
                          'oxford university press', 'jps', 'physical society of japan', 'springer', 'sif',
                          'societa italiana di fisica', ]

    forbidden_patterns = ['.{0, 10}'.join(x) for x in itertools.product(start_patterns, forbidden_patterns)]

    return __find_regexp_in_pdf(extra_data, needed_patterns, forbidden_patterns)


def _cc_licence(obj, extra_data):
    """Check if publication has 'cc by' or 'creative commons attribution' marking *in pdf(a) file* """
    patterns = ['cc.?by', 'creative.?commons.?attribution', ]
    return __find_regexp_in_pdf(extra_data, patterns)


COMPLIANCE_TASKS = [
    ('Files', _files),
    ('Received in time', _received_in_time),
    ('Funded by', _funded_by),
    ('Author rights', _author_rights),
    ('Licence', _cc_licence),
]


def check_compliance(obj, eng):
    checks = {}

    recid = obj.data['control_number']
    pid = PersistentIdentifier.get('recid', recid)

    if '_files' not in obj.data:
        obj.data['_files'] = Record.get_record(pid.object_uuid)['_files']

    # Add temporary data to evalutaion
    extra_data = {'extracted_text': __extract_article_text(obj)}

    all_checks_accepted = True
    for name, func in COMPLIANCE_TASKS:
        check_accepted, details, debug = func(obj, extra_data)
        all_checks_accepted = all_checks_accepted and check_accepted
        checks[name] = {
            'check': check_accepted,
            'details': details,
            'debug': debug
        }

    c = Compliance()
    results = {
        'checks': checks,
        'accepted': all_checks_accepted,
        'data': {
            'doi': obj.data['dois'][0]['value'],
            'publisher': obj.data['imprints'][0]['publisher'],
            'arxiv': __get_first_arxiv(obj)
        }
    }

    c.results = results
    c.id_record = pid.object_uuid

    db.session.add(c)
    db.session.commit()

    # send notification about failed checks
    if not all_checks_accepted:
        msg = TemplatedMessage(
            template_html='scoap3_compliance/admin/failed_email.html',
            subject='SCOAP3 - Compliance check',
            sender=current_app.config.get('DEFAULT_FROM_EMAIL'),
            recipients=current_app.config.get('COMPLIANCE_EMAILS'),
            ctx={'results': results}
        )
        current_app.extensions['mail'].send(msg)
