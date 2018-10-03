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


def __extract_text_as_extra_data(obj):
    # fixme extraction shouldn't happen in article_upload?
    # do extraction only if not done earlier
    if 'extracted_data' in obj.extra_data:
        return

    obj.extra_data['extracted_data'] = {}
    for file in obj.data['_files']:
        filetype = file['filetype']
        if filetype in ('pdf', 'pdf/a'):
            path = ObjectVersion.get(file['bucket'], file['key']).file.uri
            try:
                obj.extra_data['extracted_data'][filetype] = extract_text_from_pdf(path).decode('utf-8')
            except PDFSyntaxError as e:
                current_app.logger.error('Error while extracting text from pdf with uri %s: %s' % (path, e))



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


def __find_regexp_in_pdf(obj, patterns, forbidden_patterns=None):
    """
    Finds all matches for given patterns with surrounding characters in all filetypes.
    Fails only if there are no matches at all or there is a match for a forbidden pattern.
    :param patterns: iterable of string patterns
    """
    __extract_text_as_extra_data(obj)

    ok = True
    details = []

    for filetype, data in obj.extra_data['extracted_data'].iteritems():
        # first check for forbidden patterns
        if forbidden_patterns:
            forbidden_matches = __find_regexp(data, forbidden_patterns)
            if forbidden_matches:
                ok = False
                details.append('Found forbidden match in %s: "%s"' % (filetype, '", "'.join(set(forbidden_matches))))

        matches = __find_regexp(data, patterns)
        if not matches:
            ok = False
            details.append('Not found in %s' % filetype)
        else:
            details.append('Found in %s as: "%s"' % (filetype, '", "'.join(set(matches))))

    return ok, details, None


def _files(obj):
    """check if it has the necessary files: .xml, .pdf, .pdfa """

    file_types = [file['filetype'] for file in obj.data['_files']]

    ok = True
    details = ''

    if 'xml' not in file_types:
        ok = False
        details += 'No xml file. '

    if 'pdf' not in file_types and 'pdf/a' not in file_types:
        ok = False
        details += 'No pdf file. '

    details += 'Available files: %s' % ', '.join(file_types)

    return ok, (details, ), None


def _received_in_time(obj):
    """check if publication is not older than 24h """
    api_url = current_app.config.get('CROSSREF_API_URL')

    api_message = requests.get(api_url % __get_first_doi(obj)).json()['message']

    if 'publication_info' in obj.data and obj.data['publication_info'][0]['journal_title'] == 'Progress of Theoretical and Experimental Physics':
        parts = api_message['published-online']['date-parts'][0]
        # only contains day of publication, check for end of day
        api_time = datetime(*parts, hour=23, minute=59, second=59)
    else:
        api_time = parse_date(api_message['created']['date-time'], ignoretz=True)
    received_time = parse_date(obj.data['acquisition_source']['date'])
    delta = received_time - api_time

    ok = delta <= timedelta(hours=24)
    details_message = 'Arrived %d hours later then creation date on crossref.org.' % (delta.total_seconds() / 3600)
    debug = 'Time from crossref: %s, Received time: %s' % (api_time, received_time)

    return ok, (details_message ,), debug


def _founded_by(obj):
    """check if publication has "Founded by SCOAP3" marking *in pdf(a) file* """

    patterns = ['scoap3?', ]
    return __find_regexp_in_pdf(obj, patterns)


def _author_rights(obj):
    COPYRIGHT = u'\N{COPYRIGHT SIGN}'

    start_patterns = (COPYRIGHT, 'copyright', '\(c\)', )

    needed_patterns = [p + '.{15}' for p in start_patterns]

    forbidden_patterns = ['iop', 'institute of physics', 'elsevier', 'hindawi', 'cas', 'chinese academy of science',
                          'sissa', 'dpg', 'deutsche physikalische gesellschaft', 'uj', 'jagiellonian university', 'oup',
                          'oxford university press', 'jps', 'physical society of japan', 'springer', 'sif',
                          'societa italiana di fisica', ]

    forbidden_patterns = ['.{0, 10}'.join(x) for x in itertools.product(start_patterns, forbidden_patterns)]

    return __find_regexp_in_pdf(obj, needed_patterns, forbidden_patterns)


def _cc_licence(obj):
    """check fif publication has 'cc by' or 'creative commons attribution' marking *in pdf(a) file* """
    patterns = ['cc.?by', 'creative.?commons.?attribution', ]
    return __find_regexp_in_pdf(obj, patterns)


COMPLIANCE_TASKS = [
    ('Files', _files),
    ('Received in time', _received_in_time),
    ('Founded by', _founded_by),
    ('Author rights', _author_rights),
    ('Licence', _cc_licence),
]


def check_compliance(obj, eng):
    checks = {}
    all_ok = True
    for name, func in COMPLIANCE_TASKS:
        ok, details, debug = func(obj)
        all_ok = all_ok and ok
        checks[name] = {
            'check': ok,
            'details': details,
            'debug': debug
        }

    c = Compliance()
    results = {
        'checks': checks,
        'accepted': all_ok,
        'data': {
            'doi': obj.data['dois'][0]['value'],
            'publisher': obj.data['imprints'][0]['publisher'],
            'arxiv': __get_first_arxiv(obj)
        }
    }

    c.results = results
    pid = PersistentIdentifier.get('recid', obj.extra_data['recid'])
    c.id_record = pid.object_uuid

    db.session.add(c)
    db.session.commit()

    # send notification about failed checks
    if not all_ok:
        msg = TemplatedMessage(
            template_html='scoap3_compliance/admin/failed_email.html',
            subject='SCOAP3 - Compliance check',
            sender=current_app.config.get('DEFAULT_FROM_EMAIL'),
            recipients=current_app.config.get('COMPLIANCE_EMAILS'),
            ctx={'results': results}
        )
        current_app.extensions['mail'].send(msg)
