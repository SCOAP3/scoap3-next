import itertools
import re
from datetime import timedelta
from dateutil.parser import parse as parse_date

import requests
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier

from scoap3.modules.compliance.models import Compliance
from scoap3.utils.pdf import extract_text_from_pdf


def __get_first_doi(obj):
    return obj.data['dois'][0]['value']


def __extract_text_as_extra_data(obj):
    # fixme extraction shouldn't happen in article_upload?
    # do extraction only if not done earlier
    if 'extracted_data' in obj.extra_data:
        return

    for file in obj.extra_data['files']:
        # TODO add pdfa extraction and checks as well
        if file['filetype'] in ('pdf', ):
            path = file['url']
            obj.extra_data['extracted_data'] = extract_text_from_pdf(path)


def __find_regexp(data, patterns):
    """Finds all matches for given patterns.
    :return list of all matches.
    """

    matches = []

    for pattern in patterns:
        # add the surrounding characters too
        pattern = "(.{0,10}%s.{0,10})" % pattern

        match = re.findall(pattern, data, re.IGNORECASE | re.DOTALL)
        for m in match:
            # it can contain a string or tuple of strings if there is multiple match groups
            if isinstance(m, tuple):
                matches.append(m[0])
            else:
                matches.append(m)

    return matches


def __find_regexp_in_pdf(obj, patterns, forbidden_patterns=None):
    """
    Finds all matches for given patterns with surrounding characters.
    Failes only if there are no matches at all.
    :param patterns: iterable of string patterns
    """
    __extract_text_as_extra_data(obj)

    # first check for forbidden patterns
    if forbidden_patterns:
        forbidden_matches =__find_regexp(obj.extra_data['extracted_data'], forbidden_patterns)
        if forbidden_matches:
            return False, 'Found forbidden match: "%s"' % '", "'.join(set(forbidden_matches)), None

    matches = __find_regexp(obj.extra_data['extracted_data'], patterns)

    if not matches:
        return False, 'Not found.', None

    details = 'Found as: "%s"' % '", "'.join(set(matches))
    return True, details, None


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

    return ok, details, None


def _received_in_time(obj):
    """check if publication is not older than 24h """
    api_url = 'https://api.crossref.org/works/%s'

    api_message = requests.get(api_url % __get_first_doi(obj)).json()['message']

    api_time = parse_date(api_message['created'])  # todo check published-online for PTEP
    received_time = parse_date(obj.data['acquisition_source']['date'])
    delta = received_time - api_time

    ok = delta <= timedelta(hours=24)
    details_message = 'Arrived %d hours later then creation date on crossref.org.' % (delta.total_seconds() / 3600)
    debug = 'Time from crossref: %s, Received time: %s' % (api_time, received_time)

    return ok, details_message, debug


def _founded_by(obj):
    """check if publication has "Founded by SCOAP3" marking *in pdf(a) file* """

    patterns = ['scoap3?', ]
    return __find_regexp_in_pdf(obj, patterns)


def _author_rights(obj):
    COPYRIGHT = u'\N{COPYRIGHT SIGN}'.encode('utf-8')

    start_patterns = (COPYRIGHT, 'copyright', '/(c/)', )

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
        'accepted': all_ok
    }

    c.results = results
    pid = PersistentIdentifier.get('recid', obj.extra_data['recid'])
    c.id_record = pid.object_uuid

    db.session.add(c)
    db.session.commit()

    # todo send notif
