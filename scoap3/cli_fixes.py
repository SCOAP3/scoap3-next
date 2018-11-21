import numbers
from HTMLParser import HTMLParser

import click
from flask.cli import with_appcontext
from invenio_db import db
from invenio_files_rest.models import ObjectVersion, Location
from invenio_pidstore.models import PersistentIdentifier
from invenio_records import Record
from invenio_search import current_search_client
from sqlalchemy.orm.attributes import flag_modified
from xml.dom.minidom import parse

from scoap3.config import COUNTRIES_DEFAULT_MAPPING
from scoap3.utils.click_logging import rerror, error, info, rinfo
from scoap3.utils.google_maps import get_country
from scoap3.utils.processor import process_all_records, process_all_articles_impact


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
def update_countries(dry_run, ids, country="HUMAN CHECK"):
    """
    Updates countries for articles, that are marked as given parameter. Countries are determined with the google maps api.
    """

    country_cache = {}
    cache_fails = 0
    total_hits = 0

    # Use parameter ids or, if not given, search for all records with the specified country.
    if ids:
        ids = ids.split(',')
    else:
        search_result = current_search_client.search('records-record', 'record-v1.0.0',
                                                     {'size': 10000, 'query': {'term': {'country': country}}})
        ids = [hit['_source']['control_number'] for hit in search_result['hits']['hits']]
        info('Found %d records having %s as a country of one of the authors.' % (len(ids), country))

    uuids = [PersistentIdentifier.get('recid', recid).object_uuid for recid in ids]
    records = Record.get_records(uuids)

    try:
        for record in records:
            for author_index, author_data in enumerate(record['authors']):
                for aff_index, aff_data in enumerate(author_data['affiliations']):
                    if aff_data['country'] == country:
                        total_hits += 1

                        # cache countries based on old affiliation value to decrease api requests
                        old_value = aff_data['value']
                        if old_value not in country_cache:
                            country_cache[old_value] = get_country(old_value)
                            cache_fails += 1

                        new_country = country_cache[old_value]

                        if new_country:
                            record['authors'][author_index]['affiliations'][aff_index]['country'] = new_country
                            info(
                                'Changed country for record with id %s to %s' % (record['control_number'], new_country))
                        else:
                            error('Could not find country for record with id %s (affiliation value: %s)' % (
                                record['control_number'], old_value))
            if not dry_run:
                record.commit()
                db.session.commit()
    except Exception as e:
        print(e)

    info('In total %d countries needed to be updated and %d queries were made to determine the countries.' % (
        total_hits, cache_fails))

    if dry_run:
        error('NO CHANGES were committed to the database, because --dry-run flag was present.')


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
    ids = (
        24958, 22783, 24213, 23544, 23575, 20026, 40533, 19858, 42820, 42098, 41691, 42268, 43140, 12224, 768, 43275,
        23538, 2142, 24522, 18606, 22009, 4879, 24855, 41724, 40950, 41119, 41793, 24332, 23328, 42942, 23475, 41849,
        24247, 23326, 40823, 41896, 24004, 40261, 23041, 43021, 43008, 42671, 41873, 42327, 40845, 3952, 42073, 41850,)

    def proc(record):
        """Fix country mappings..."""

        if 'authors' in record.json:
            for i, a in enumerate(record.json['authors']):
                for i2, aff in enumerate(a.get('affiliations', ())):
                    c = aff['country']
                    new_c = COUNTRIES_DEFAULT_MAPPING.get(c, c)
                    if c != new_c:
                        rinfo('%s -> %s' % (c, new_c), record)
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
    ids = (
        18758, 19841, 21407, 21896, 22903, 24301, 40311, 23504, 23866, 23613, 23661, 23861, 23725, 24005, 23867, 15590,
        16071, 15938, 15943, 15867, 15931, 16014, 15940, 15942, 16196, 15851, 15817, 15789, 15790, 15745, 25282, 25288,
        24955, 25442, 25376, 25346, 25277, 40576, 40629, 40677, 40680, 40813, 23974, 24958, 24932, 40833, 25272, 25265,
        24434, 25301, 25303, 25299, 25261, 24811, 24810, 24809, 24860, 24848, 24815, 24825, 24571, 40834, 40766, 40838,
        40900, 40906, 23424, 23411, 23237, 23040, 23195, 23060, 23221, 23414, 23081, 23419, 23130, 23134, 23211, 23017,
        23451, 23235, 40240, 40279, 40288, 40487, 40435, 25292, 25426, 25400, 25399, 25522, 40392, 40583, 40575, 40665,
        40245, 40242, 25309, 40633, 25467, 25468, 25471, 40678, 40291, 40285, 40343, 25328, 25445, 40910, 40911, 40679,
        40540, 40812, 40839, 40438, 40728, 40681, 40884, 40885, 40858, 40932, 40901, 40904, 40928, 40962, 40963, 41570,
        41572, 41573, 41585, 41588, 41594, 41595, 41598, 41599, 41601, 41602, 41605, 41612, 41613, 41617, 41618, 41627,
        41628, 41631, 41637, 41640, 41641, 41678, 41692, 41702, 41740, 41810, 41837, 41857, 41944, 41977, 41979, 42005,
        42049, 42050, 42099, 42116, 42155, 42156, 42174, 42215, 42221, 42225, 42259, 42286, 42300, 42307, 42308, 42341,
        42344, 42351, 42385, 42422, 42424, 42456, 42458, 42485, 42505, 43068, 43070, 43071, 43072, 43080, 43082, 43084,
        43089, 43092, 43093, 43096, 43098, 43109, 43110, 43113, 43114, 43116, 43118, 43120, 43121, 43127, 43129, 43150,
        43154, 43170, 43171, 43173, 43174, 43176, 43200, 43213, 43224, 43226, 43227, 43230, 43237, 43269, 43288, 43290,
        43303, 43305, 43314,)

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
            rerror('Skipping. MORE THEN ONE author group. Not supported.', record)
            return

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
                        {u'country': get_country_for_aff(a),
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
def init_default_location():
    """Add default Location, if not already present."""

    if not Location.query.filter(Location.name == 'default').count():
        loc = Location()
        loc.name = 'default'
        loc.default = True
        loc.uri = '/virtualenv/files/'
        db.session.add(loc)
        db.session.commit()
    else:
        error("Default location already exists.")
