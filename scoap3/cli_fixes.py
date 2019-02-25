import csv

from StringIO import StringIO

from flask import current_app
import json
import numbers
import tarfile
from datetime import datetime, timedelta
from os import listdir
from os.path import isfile, getctime
from zipfile import ZipFile, BadZipfile

import six
from HTMLParser import HTMLParser

import click
from dateutil.parser import parse as parse_date
from flask.cli import with_appcontext
from invenio_db import db
from invenio_files_rest.models import ObjectVersion, Location
from invenio_pidstore.models import PersistentIdentifier
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_records import Record
from invenio_search.api import current_search_client as es
from pyexpat import ExpatError
from sqlalchemy.orm.attributes import flag_modified
from xml.dom.minidom import parse, parseString

from scoap3.config import COUNTRIES_DEFAULT_MAPPING
from scoap3.dojson.utils.nations import find_country
from scoap3.modules.analysis.models import Gdp
from scoap3.modules.records.util import get_first_doi
from scoap3.utils.arxiv import get_arxiv_categories
from scoap3.utils.click_logging import rerror, error, info, rinfo
from scoap3.utils.google_maps import get_country
from scoap3.utils.http import requests_retry_session
from scoap3.utils.processor import process_all_records, process_all_articles_impact

from scoap3.modules.records.util import get_arxiv_primary_category


@click.group()
def fixdb():
    """Database fix commands."""


@fixdb.command()
@with_appcontext
@click.option('--ids', default=None, help="Comma separated list of recids to be processed. eg. '98,324'")
def unescaperecords(ids):
    """HTML unescape abstract and title for all records."""

    parser = HTMLParser()

    def proc(record, parser):
        if record.json is None:
            rerror('record.json is None', record)
            return

        unescape_abstract(record, parser)
        unescape_titles(record, parser)

    if ids:
        ids = ids.split(',')

    process_all_records(proc, 50, ids, parser)

    info('all done!')


def unescape_abstract(record, parser):
    if 'abstracts' not in record.json or len(record.json['abstracts']) == 0:
        rerror('Record has no abstracts.', record)
        return

    if len(record.json['abstracts']) > 1:
        rerror('Record has more then one abstracts (%d). Skipping.' % len(record.json['abstracts']), record)
        return

    original = record.json['abstracts'][0]['value']
    unescaped = parser.unescape(original)
    if unescaped != original:
        rinfo('Abstract changed.', record)
        record.json['abstracts'][0]['value'] = unescaped
        flag_modified(record, 'json')


def unescape_titles(record, parser):
    if 'titles' not in record.json or len(record.json['titles']) == 0:
        rerror('Record has no titles.', record)
        return

    original = record.json['titles']
    unescaped = []

    for title in original:
        if 'title' not in title:
            rerror('title key not in title', record)

        title['title'] = parser.unescape(title['title'])
        unescaped.append(title)

    if unescaped != original:
        rinfo('Authors changed.', record)
        record.json['titles'] = unescaped
        flag_modified(record, 'json')


def utf8rec(data):
    if isinstance(data, basestring):
        try:
            return ''.join(chr(ord(c)) for c in data).decode('utf8')
        except:  # noqa todo: implement proper exception handling (E722 do not use bare except)
            return data

    if isinstance(data, tuple) or isinstance(data, list):
        return [utf8rec(element) for element in data]

    if isinstance(data, dict):
        return {k: utf8rec(v) for k, v in data.items()}

    if isinstance(data, numbers.Number) or data is None:
        return data

    error('Couldn\'t determine the data type of %s. Returning the same.' % data)
    return data


@fixdb.command()
@with_appcontext
@click.option('--ids', default=None, help="Comma separated list of recids to be processed. eg. '98,324'")
def utf8(ids):
    """Unescape records and store data as unicode."""

    def proc(record):
        if record.json is None:
            rerror('record.json is None', record)
            return
        record.json = utf8rec(record.json)
        flag_modified(record, 'json')

    if ids:
        ids = ids.split(',')

    process_all_records(proc, control_ids=ids)
    info('all done!')


@fixdb.command()
@click.option('--dry-run', is_flag=True, default=False,
              help='If set to True no changes will be committed to the database.')
@click.option('--ids', default=None, help="Comma separated list of recids to be processed. eg. '98,324'")
@with_appcontext
def update_countries(dry_run, ids):
    """
    Updates countries for articles, that are marked as given parameter. Countries are determined with the google maps api.
    """

    counts = {'changed': 0, 'all': 0}

    if ids:
        ids = ids.split(',')

    def proc(record):
        try:
            if 'authors' not in record.json:
                error('no authors for record %s' % record.json['control_number'])
                return

            for author_index, author_data in enumerate(record.json['authors']):
                if 'affiliations' not in author_data:
                    error('no affiliations for record %s' % record.json['control_number'])
                    continue

                for aff_index, aff_data in enumerate(author_data['affiliations']):
                    counts['all'] += 1

                    new_country = find_country(aff_data['value'])
                    if aff_data['country'] != new_country:
                        counts['changed'] += 1

                        info('Changed country for record with id %s from %s to %s' % (record.json['control_number'],
                                                                                      aff_data['country'], new_country))
                        record.json['authors'][author_index]['affiliations'][aff_index]['country'] = new_country

            if not dry_run:
                flag_modified(record, 'json')
        except Exception as e:
            error(str(e))

    process_all_records(proc, control_ids=ids)

    if dry_run:
        error('NO CHANGES were committed to the database, because --dry-run flag was present.')

    info("%s\nDONE." % counts)


def get_country_for_aff(x_aff):
    # In XML could have other representations for certain organizations?
    ORGS = ('CERN', 'JINR',)

    organizations = [c.childNodes[0].nodeValue for c in x_aff.getElementsByTagName('sa:organization')]
    common = set(organizations).intersection(ORGS)
    if common:
        return common.pop()

    country = x_aff.getElementsByTagName('sa:country')
    if country:
        return country[0].childNodes[0].nodeValue

    info('No country in XML. Falling back to google maps.')
    country = get_country(x_aff.getElementsByTagName('ce:textfn')[0].childNodes[0].nodeValue)
    if country:
        return country

    error('Google didn\'t help.')
    return 'HUMAN CHECK'


def update_authors(record, authors, new_affs):
    # matching authors is not rly possible.
    raise NotImplementedError
    updated = 0
    for i, a in enumerate(record.json.get('authors')):
        if (a['given_names'], a['surname']) in authors:
            updated += 1
            # TODO add new affiliations

    assert (updated == len(authors))


@fixdb.command()
@with_appcontext
def hotfix_country_mapping():
    ids = (29476, 44219, 44220)

    def proc(record):
        """Fix country mappings..."""

        if record.json and 'authors' in record.json:
            for i, a in enumerate(record.json['authors']):
                for i2, aff in enumerate(a.get('affiliations', ())):

                    c = aff.get('country')
                    new_c = find_country(aff['value'])
                    if c != new_c:
                        rinfo('%s -> %s (%s)' % (c, new_c, aff['value']), record)
                        record.json['authors'][i]['affiliations'][i2]['country'] = new_c
                        flag_modified(record, 'json')

    process_all_records(proc, control_ids=ids)
    info('ALL DONE')


@fixdb.command()
@with_appcontext
def hotfix_country_mapping_in_article_impacts():
    def proc(r):
        for k, v in dict(r.results).iteritems():
            new_k = COUNTRIES_DEFAULT_MAPPING.get(k, k)
            if k != new_k:
                info('%d: %s => %s' % (r.control_number, k, new_k))
                r.results[new_k] = v
                r.results.pop(k)
                flag_modified(r, 'results')

    process_all_articles_impact(proc)
    info('ALL DONE')


@fixdb.command()
@with_appcontext
def hotfix_els_countries():
    """Hotfix for updating countries from xml"""
    ids = (44264, 24944, 24850, 16040, 23414, 15632, 15820, 24786, 15937, 25306, 15819, 40393, 15681, 23089, 23019)

    def get_aff_by_id(x_author_group, aff_id):
        for x_affiliation in x_author_group.getElementsByTagName('ce:affiliation'):
            id = x_affiliation.attributes.get('id').value
            if id == aff_id:
                return x_affiliation.getElementsByTagName('ce:textfn')[0].childNodes[0].nodeValue

        error('No affiliation for id: %s' % aff_id)
        return None

    def proc(record):
        rinfo('start...', record)

        if '_files' not in record.json:
            rerror('Skipping. No _files', record)
            return

        xml = filter(lambda x: x['filetype'] == 'xml', record.json['_files'])
        if not xml:
            rerror('Skipping. No xml in _files', record)
            return

        object = ObjectVersion.get(xml[0]['bucket'], xml[0]['key'])
        uri = object.file.uri
        xml = parse(open(uri, 'rt'))
        x_author_groups = xml.getElementsByTagName('ce:author-group')

        if not x_author_groups:
            rerror('Skipping. No author groups.', record)
            return

        if len(x_author_groups) > 1:
            rinfo('Reparse all authors.', record)
            authors = []

            for x_author_group in x_author_groups:
                # skip if not deepest author-group
                if x_author_group.getElementsByTagName('ce:author-group'):
                    continue

                # extract affiliations
                x_affiliations = x_author_group.getElementsByTagName('ce:affiliation')
                affs = []
                for a in x_affiliations:
                    value = a.getElementsByTagName('ce:textfn')[0].childNodes[0].nodeValue
                    affs.append({
                        u'country': find_country(value),
                        u'value': value
                    })

                # extract authors, add affiliations
                x_authors = x_author_group.getElementsByTagName('ce:author')
                for x_author in x_authors:
                    given_name = x_author.getElementsByTagName('ce:given-name')[0].childNodes[0].nodeValue
                    surname = x_author.getElementsByTagName('ce:surname')[0].childNodes[0].nodeValue
                    full_name = '%s, %s' % (surname, given_name)

                    author_affs = []
                    for ref in x_author.getElementsByTagName('ce:cross-ref'):
                        affid = ref.attributes.get('refid').value
                        if 'aff' in affid:
                            aff_value = get_aff_by_id(x_author_group, affid)
                            aff_country = find_country(aff_value)
                            author_affs.append({
                                u'country': aff_country,
                                u'value': aff_value
                            })

                    if not (author_affs or affs):
                        rerror('no affs for author: %s. Skip this record.' % surname, record)
                        return

                    authors.append({
                        'full_name': full_name,
                        'given_name': given_name,
                        'surname': surname,
                        'affiliations': author_affs or affs
                    })

            if authors:
                record.json['authors'] = authors
                flag_modified(record, 'json')
                rinfo('updated', record)
            else:
                rerror('No authors found', record)

        else:
            for x_author_group in x_author_groups:
                x_collaborations = x_author_group.getElementsByTagName('ce:collaboration')
                x_affiliations = x_author_group.getElementsByTagName('ce:affiliation')
                # needed for supporting multiple author groups with author matching, but author matching is not rly possible.
                # authors_in_group = [
                #     (c.getElementsByTagName('ce:given-name')[0].childNodes[0].nodeValue.replace('-', '').title(),
                #      c.getElementsByTagName('ce:surname')[0].childNodes[0].nodeValue.replace('-', '').title())
                #     for c in x_author_group.getElementsByTagName('ce:author')
                # ]

                if 'authors' not in record.json:
                    # Type 1 and 3: has no authors at all. Fix: add collaborations if there are affiliations in xml.
                    rerror('No authors... SKIPPING', record)
                    return

                    # extract collaborations, find countries later
                    # FIXME we should always extract collaborations, but that would cause a lot more problems now.
                    authors = [{'full_name': c.getElementsByTagName('ce:text')[0].childNodes[0].nodeValue} for c in
                               x_collaborations]
                    if authors:
                        rinfo('Collaborations found: %s' % authors, record)
                        record.json['authors'] = authors
                    else:
                        rerror('No collaborations. Not fixable.', record)

                # possibly we added authors in the previous step.
                if 'authors' in record.json:
                    # Type 2 and 4: has authors, but no affiliations.
                    authors = record.json['authors']
                    aff_count = sum(map(lambda x: 'affiliations' in x, authors))
                    if aff_count == 0:
                        # Type 4: No affiliations in data.
                        new_affs = [
                            {u'country': find_country(a.getElementsByTagName('ce:textfn')[0].childNodes[0].nodeValue),
                             u'value': a.getElementsByTagName('ce:textfn')[0].childNodes[0].nodeValue
                             }
                            for a in x_affiliations]
                        if new_affs:
                            rinfo('New affiliations: %s' % new_affs, record)
                            # FIXME modify this, if multiple author groups should be supported
                            # FIXME (not all authors should be updated)!!!
                            # update_authors(record, authors_in_group, new_affs)

                            for i, a in enumerate(record.json.get('authors')):
                                record.json['authors'][i]['affiliations'] = new_affs
                            flag_modified(record, 'json')
                        else:
                            rerror('No affiliations at all. Not fixable.', record)

                    elif aff_count == len(authors):
                        empty_aff_count = sum(map(lambda x: len(x['affiliations']) == 0, authors))
                        if empty_aff_count == len(authors):
                            # Type 2: Only empty affiliations.
                            rinfo('Type 2. Not fixable.', record)
                        else:
                            rerror('Only SOME authors have EMPTY affiliations. What now?', record)
                    else:
                        rerror('Only SOME authors have affiliations. What now?', record)

        rinfo('OK', record)

    process_all_records(proc, control_ids=ids)
    info('ALL DONE')


@fixdb.command()
@with_appcontext
def extract_year_from_record_creation():
    def proc(record):
        if not record.json:
            rerror('no json.', record)
            return

        if 'record_creation_year' not in record.json:
            date = parse_date(record.json['record_creation_date'])
            if not date:
                rerror("Date couldn't be parsed: %s" % record.json['record_creation_date'], record)

            record.json['record_creation_year'] = date.year
            flag_modified(record, 'json')

    process_all_records(proc)
    info('ALL DONE')


@fixdb.command()
@with_appcontext
def init_default_location():
    """
    Add default Location, if not already present.
    Used by Travis as well.
    """

    if not Location.query.filter(Location.name == 'default').count():
        loc = Location()
        loc.name = 'default'
        loc.default = True
        loc.uri = '/virtualenv/files/'
        db.session.add(loc)
        db.session.commit()
    else:
        error("Default location already exists.")


@fixdb.command()
@with_appcontext
def repos_diff():
    OLD_REPO_FILE = '/tmp/old_repo_dump4'
    OLD_REPO_URL = 'https://repo.scoap3.org/search?p=&of=recjson&ot=recid,doi,creation_date&rg=100000000'
    COOKIES = {
        'INVENIOSESSION': 'd3c673cf6be468dc6c6fd25703ff90c3',
        'INVENIOSESSIONstub': 'HTTPS',
        '_pk_id.10.1cdf': 'ff8bdd9962372712.1536586766.49.1546956598.1546955767.'
    }
    RESULT_FILE = '/tmp/repo_diff_result9'

    if not isfile(OLD_REPO_FILE):
        info('No old repo file (%s), downloding...' % OLD_REPO_FILE)
        data = requests_retry_session().get(OLD_REPO_URL, cookies=COOKIES).json()
        info('download complete (%d records), mapping...' % len(data))

        if len(data) < 1000:
            error('Aborting, not all record queried.')
            return

        mapped_data = {}
        for r in data:
            doi = r.pop('doi')
            if doi in mapped_data:
                error('Multiple records with doi. %s' % r)
            mapped_data[doi] = r

        info('mapping complete, saving file...')
        with open(OLD_REPO_FILE, 'wt') as f:
            f.write(json.dumps(mapped_data))

        info('File saved.')

    info('reading old repo data from: %s' % OLD_REPO_FILE)
    with open(OLD_REPO_FILE, 'rt') as f:
        old_data = json.loads(f.read())

    result = dict(only_in_old=[],
                  only_in_new=[],
                  in_both=[])

    def proc(record):
        if not record.json:
            return

        doi = get_first_doi(record.json)
        if doi in old_data:
            result['in_both'].append(doi)
            old_data.pop(doi)
        else:
            result['only_in_new'].append(doi)

    process_all_records(proc)

    result['only_in_old'] = map(lambda x: x[0], old_data.iteritems())
    with open(RESULT_FILE, 'wt') as f:
        f.write(json.dumps(result, indent=2))

    info('only_in_old: %s\nonly_in_new: %s\nin_both:%s\nALL DONE.' % (
        len(result['only_in_old']), len(result['only_in_new']), len(result['in_both'])))


@fixdb.command()
@with_appcontext
def springer():
    DIR = 'JHEP/'
    EXT = ('.xml.Meta', '.xml.scoap')
    BASE_DIR = '/eos/project/s/scoap3repo/BETA/harvesting/Springer/download/' + DIR
    zip_list = listdir(BASE_DIR)

    needed_dois = json.loads(open('/tmp/repo_diff_result2', 'r').read())['only_in_old']

    extracted_dois = {}
    for file in zip_list:
        full_path = BASE_DIR + file
        if isfile(full_path) and full_path.endswith('.zip'):
            try:
                zip = ZipFile(full_path)
                for zip_element in zip.infolist():
                    fn = zip_element.filename
                    if fn.endswith(EXT):
                        xml = parseString(zip.read(zip_element))
                        doi = xml.getElementsByTagName('ArticleDOI')[0].firstChild.nodeValue
                        if doi in needed_dois:
                            if full_path not in extracted_dois:
                                extracted_dois[full_path] = []
                            extracted_dois[full_path].append(doi)
            except BadZipfile as e:
                error('file %s: %s' % (file, e))

    info('%s' % json.dumps(extracted_dois, indent=2))


@fixdb.command()
@with_appcontext
def elsevier():
    EXT = 'main.xml'
    BASE_DIR = '/eos/project/s/scoap3repo/BETA/harvesting/Elsevier/download/'
    RESULT_FILE = '/tmp/elsevier'
    tar_list = listdir(BASE_DIR)
    needed_dois = json.loads(open('/tmp/repo_diff_result5', 'r').read())['only_in_old']

    from_date = datetime.now() - timedelta(days=365)
    to_date = datetime.now() - timedelta(days=60)
    info('found %d files in base dir.' % len(tar_list))

    extracted_dois = {}
    for file in tar_list:
        full_path = BASE_DIR + file
        creation_date = datetime.utcfromtimestamp(getctime(full_path))
        if isfile(full_path) and full_path.endswith('.tar') and from_date <= creation_date <= to_date:
            try:
                tar = tarfile.open(full_path, 'r')
                for element in tar.getmembers():
                    if element.name.endswith(EXT):
                        xml = parseString(tar.extractfile(element).read())
                        doi = xml.getElementsByTagName('item-info')[0].getElementsByTagName('ce:doi')[0].firstChild.nodeValue
                        if doi in needed_dois:
                            if full_path not in extracted_dois:
                                extracted_dois[full_path] = []
                            extracted_dois[full_path].append(doi)
                            info('found %s in %s' % (doi, file))
                    else:
                        pass
                        # info('ignoring file: %s' % fn)
            except (tarfile.TarError, ExpatError) as e:
                error('file %s: %s' % (file, e))

    info('%s' % json.dumps(extracted_dois, indent=2))

    with open(RESULT_FILE, 'wt') as f:
        f.write(json.dumps(extracted_dois, indent=2))


@fixdb.command()
@with_appcontext
def add_primary_arxiv_categories():
    def proc(article_impact):
        try:
            if 'arxiv_primary_category' in article_impact.details:
                return

            pid = PersistentIdentifier.get('recid', article_impact.control_number)
            record = Record.get_record(pid.object_uuid)

            if not record:
                return

            if 'arxiv_eprints' in record:
                info('%d: eprints found' % article_impact.control_number)
                arxiv = (record['arxiv_eprints'][0]['value'].split(':')[1]).split('v')[0]
                cat = get_arxiv_categories(arxiv)[0]
                info('category: %s' % cat)
                if cat:
                    article_impact.details['arxiv_primary_category'] = cat
                    flag_modified(article_impact, 'details')

            elif 'report_numbers' in record:
                info('%d: report_numbers found' % article_impact.control_number)
                cat = get_arxiv_primary_category(record)
                info('category: %s' % cat)
                if cat:
                    article_impact.details['arxiv_primary_category'] = cat
                    flag_modified(article_impact, 'details')

            else:
                error('%d: no arxiv' % article_impact.control_number)

        except PIDDoesNotExistError:
            # records imported from Inspire won't be found
            pass
        except AttributeError as e:
            error('%d: %s' % (article_impact.control_number, e))

    process_all_articles_impact(proc)

    info('DONE.')


@fixdb.command()
@with_appcontext
def check_authors():
    RESULT_FILE = '/tmp/check_authors'
    result = {
        'null': set(),
        'noauth': set(),
        'noaff': set(),
        'nocountry': set(),
        'empty_aff': set()
    }

    def proc(record):
        key = ''
        if not record.json:
            key = 'null'
        elif 'authors' not in record.json:
            key = 'noauth'
        else:
            for a in record.json['authors']:
                if 'affiliations' not in a:
                    key = 'noaff'
                    break
                elif not a['affiliations']:
                    key = 'empty_aff'
                    break
                else:
                    for aff in a['affiliations']:
                        if 'country' not in aff:
                            key = 'nocountry'
                            break

        if key:
            result[key].add(record.id)

    process_all_records(proc)

    for k, v in result.items():
        pids = PersistentIdentifier.query\
            .filter(PersistentIdentifier.pid_type == 'recid')\
            .filter(PersistentIdentifier.object_uuid.in_(v)).all()
        result[k+'_c'] = map(lambda x: x.pid_value, pids)
        result[k] = map(six.text_type, v)

    result_str = json.dumps(result, indent=2)
    with open(RESULT_FILE, 'wt') as f:
        f.write(result_str)
    info(result_str)
    info('DONE')


@fixdb.command()
@with_appcontext
def check_country_share():
    RESULT_FILE = '/tmp/cs_test'

    data = {'countries': {},
            'not_one': set()}

    def proc(article_impact):
        for country, val in article_impact.results.items():
            if country not in data['countries']:
                data['countries'][country] = 0

            data['countries'][country] += val

        try:
            record = Record.get_record(PersistentIdentifier.get('recid', article_impact.control_number).object_uuid)
            author_count = len(record['authors'])
        except PIDDoesNotExistError:
            author_count = len(article_impact.details['authors'])

        sum_values = sum(article_impact.results.values())
        if sum_values != author_count:
            data['not_one'].add((article_impact.control_number, sum_values, author_count))

    process_all_articles_impact(proc)

    data['not_one'] = list(data['not_one'])

    data['missing_gdp'] = []
    all_country = [g.name for g in Gdp.query.all()]
    for c in data['countries'].keys():
        if c not in all_country:
            data['missing_gdp'].append(c)

    data['countries'] = sorted(data['countries'].items(), key=lambda x: x[0])
    result_str = json.dumps(data, indent=2)
    with open(RESULT_FILE, 'wt') as f:
        f.write(result_str)

    info('DONE')


@fixdb.command()
@with_appcontext
def empty_author():
    missing_authors = []

    def proc_find(record):
        if record.json and 'authors' in record.json:
            for a in record.json['authors']:
                s = sum(map(bool, a.values()))
                if s == 0:
                    rerror('error', record)
                    missing_authors.append(record.id)
                    return

    # process_all_records(proc_find)
    # missing_authors2 = list(map(lambda recid:PersistentIdentifier.query\
    # .filter(PersistentIdentifier.pid_type == 'recid')\
    # .filter(PersistentIdentifier.object_uuid == recid).one().pid_value, missing_authors))
    # info(json.dumps(missing_authors2, indent=2))

    def proc_delete(record):
        to_delete = []
        for i, a in enumerate(record.json['authors']):
            s = sum(map(bool, a.values()))
            if s == 0:
                to_delete.append(i)

        if to_delete:
            for d in to_delete:
                del record.json['authors'][d]
            flag_modified(record, 'json')
        info('DELETE %d authors' % len(to_delete))

    control_ids = [22647, 21193, 14535, 10195, 16281, 16197, 9110, 4336, 21274, 22399, 1156, 14391, 22126, 22633,
                   22433, 22217, 10402, 22208, 20511, 3059, 2926, 4780, 1232, 2513, 22388, 10523, 22606, 12874,
                   22853, 22789, 4021, 13026, 3073, 1899, 20297, 4185, 1311, 23074]
    process_all_records(proc_delete, control_ids=control_ids)

    info('done')


@fixdb.command()
@with_appcontext
def check_ai():
    crossref_url = current_app.config.get('CROSSREF_API_URL')

    result = {'not200': [], 'hit': []}

    def proc(ai):
        try:
            PersistentIdentifier.get('recid', ai.control_number)
        except PIDDoesNotExistError:
            api_response = requests_retry_session().get(crossref_url % ai.doi)
            if api_response.status_code != 200:
                error('Failed to query crossref for doi: %s. Error code: %s' % (ai.doi, api_response.status_code))
                result['not200'].append(ai.control_number)
                return None

            title = api_response.json()['message']['title'][0].lower()

            if 'addendum' in title or 'corrigendum' in title or 'erratum' in title:
                result['hit'].append((ai.control_number, title))

    process_all_articles_impact(proc)
    print(json.dumps(result, indent=2))


@fixdb.command()
@with_appcontext
def japanise():
    size = 100

    def get_query(start_index, size):
        return {
            '_source': ['authors', 'control_number', 'dois', 'publication_info', 'report_numbers', 'arxiv_eprints'],
            'from': start_index,
            'size': size,
            'query': {
                'term': {
                    'country': 'Japan'
                }
            }
        }

    def get_arxiv(data):
        if 'report_numbers' in data:
            for r in data['report_numbers']:
                if r['source'] == 'arXiv':
                    return r['value'].split(':')[1]
            error('no arxiv? %s' % data['control_number'])
        if 'arxiv_eprints' in data:
            return data['arxiv_eprints'][0]['value'].split(':')[1]

        return ''

    index = 0
    total = None

    header = ['year', 'journal', 'doi', 'arxiv number', 'primary arxiv category', 'affiliaton',
              'authors with affiliation', 'total number of authors']
    si = StringIO()
    cw = csv.writer(si, delimiter=";")
    cw.writerow(header)

    while total is None or index < total:
        search_results = es.search(index='records-record',
                                   doc_type='record-v1.0.0',
                                   body=get_query(index, size))
        total = search_results['hits']['total']
        info("%s/%s" % (index, total))
        index += size

        for hit in search_results['hits']['hits']:
            data = hit['_source']

            year = data['publication_info'][0]['year']
            journal = data['publication_info'][0]['journal_title']
            doi = data['dois'][0]['value']
            arxiv = get_arxiv(data)
            arxiv_category = get_arxiv_categories(arxiv)[0] if arxiv else ''

            total_authors = len(data['authors'])

            extracted_affiliations = {}
            for author in data['authors']:
                if 'affiliations' not in author:
                    error('no affiliations for author. %s' % doi)
                    continue

                for aff in author['affiliations']:
                    if aff['country'] == 'Japan':
                        value = aff['value']
                        if value not in extracted_affiliations:
                            extracted_affiliations[value] = 0
                        extracted_affiliations[value] += 1

            if not extracted_affiliations:
                error('no extracted affs')

            for aff, count in extracted_affiliations.items():
                cw.writerow([year, journal, doi, arxiv, arxiv_category, aff.encode('utf8'), count, total_authors])

    with open('/tmp/japanise.csv', 'wt') as f:
        f.write(si.getvalue())
