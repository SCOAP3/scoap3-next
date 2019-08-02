import requests_mock
from mock import patch
from pytest import raises
from workflow.errors import HaltProcessing

from scoap3.modules.workflows.workflows.articles_upload import validate_record, get_first_doi, remove_orcid_prefix
from tests.responses import read_hep_schema, read_titles_schema


def mock_halt(msg, eng):
    raise HaltProcessing(msg)


class MockObj():
    def __init__(self, data):
        self.data = data


def run_validate(data):
    eng = None
    obj = MockObj(data)

    with patch('scoap3.modules.workflows.workflows.articles_upload.__halt_and_notify', mock_halt), \
            requests_mock.Mocker() as m:
        m.register_uri('GET', '/schemas/hep.json', content=read_hep_schema())
        m.register_uri('GET', '/schemas/elements/titles.json', content=read_titles_schema())
        validate_record(obj, eng)


def test_validate_no_schema():
    data = {}

    with raises(HaltProcessing):
        run_validate(data)


def test_validate_empty_record():
    data = {'$schema': 'http://localhost/schemas/hep.json'}

    with raises(HaltProcessing):
        run_validate(data)


def test_validate_required_and_extra_fields():
    data = {
        '$schema': 'http://localhost/schemas/hep.json',
        'abstracts': [{'source': 'Springer',
                       'value': 'We present a dedicated complementarity study of gravita[...]'}],
        'authors': [{'affiliations': [{'country': 'Brazil',
                                       'organization': u'Universidade Federal de S\xe3o Paulo',
                                       'value': u'Departamento de F\xedsica, Universidade Federal de S\xe3o Paulo,'
                                                u' UNIFESP, Diadema, Brazil'}],
                     'email': 'aalves@unifesp.br',
                     'full_name': 'Alves, Alexandre',
                     'given_names': 'Alexandre',
                     'surname': 'Alves'},
                    ],
        'copyright': [{'holder': 'The Author(s)',
                       'year': '2019'}],
        'dois': [{'value': '10.1007/JHEP04(2019)052'}],
        'imprints': [{'date': '2019-04-05', 'publisher': 'Springer'}],
        'license': [{'license': 'CC-BY-3.0',
                     'url': 'https://creativecommons.org/licenses/by/3.0'}],
        'publication_info': [{'artid': 'JHEP042019052',
                              'journal_issue': '4',
                              'journal_title': 'Journal of High Energy Physics',
                              'journal_volume': '2019',
                              'material': 'article',
                              'page_end': '40',
                              'page_start': '1',
                              'year': 2019}],
        'titles': [{'source': 'Springer',
                    'title': 'Collider and gravitational wave complementarity in exploring the [...]'}],

        'should_not_be_here': True,
    }
    with raises(HaltProcessing):
        run_validate(data)


def test_validate_required_fields():
    data = {
        '$schema': 'http://localhost/schemas/hep.json',
        '_files': [{'bucket': 'c515e79e-d155-4d02-a720-38a61b755e3b',
                    'checksum': 'md5:7c88a25b46dd3d56f1abe0652480f33c',
                    'filetype': 'xml',
                    'key': '10.1007/JHEP04(2019)052.xml',
                    'size': 12459,
                    'version_id': '65e3dd96-f916-4479-b10e-6754b6cbc3f6'},
                   {'bucket': 'c515e79e-d155-4d02-a720-38a61b755e3b',
                    'checksum': 'md5:998ae8e6a550682deb161d627f36c6fc',
                    'filetype': 'pdf/a',
                    'key': '10.1007/JHEP04(2019)052_a.pdf',
                    'size': 10050434,
                    'version_id': '2fa2d949-01d6-4ca9-90db-a3ef7896dd7f'}],
        '_oai': {'id': 'oai:repo.scoap3.org:46684',
                 'sets': ['JHEP'],
                 'updated': '2019-04-08T12:33:38Z'},
        'abstracts': [{'source': 'Springer',
                       'value': 'We present a dedicated complementarity study of gravita[...]'}],
        'acquisition_source': {'date': '2019-04-08T14:30:41.101696',
                               'method': 'Springer',
                               'source': 'Springer',
                               'submission_number': '09e474c259fa11e9b28402163e01809a'},
        'arxiv_eprints': [{'categories': ['hep-ph', 'astro-ph.CO'],
                           'value': '1812.09333'}],
        'authors': [{'affiliations': [{'country': 'Brazil',
                                       'organization': u'Universidade Federal de S\xe3o Paulo',
                                       'value': u'Departamento de F\xedsica, Universidade Federal de S\xe3o Paulo,'
                                                u' UNIFESP, Diadema, Brazil'}],
                     'email': 'aalves@unifesp.br',
                     'full_name': 'Alves, Alexandre',
                     'given_names': 'Alexandre',
                     'surname': 'Alves'},
                    {'affiliations': [{'country': 'USA',
                                       'organization': 'University of Hawaii',
                                       'value': 'Department of Physics & Astronomy, University of Hawaii, Honolulu, '
                                                'HI, 96822, U.S.A.'}],
                     'email': 'tghosh@hawaii.ed',
                     'full_name': 'Ghosh, Tathagata',
                     'given_names': 'Tathagata',
                     'surname': 'Ghosh'},
                    {'affiliations': [{'country': 'USA',
                                       'organization': 'University of Oklahoma',
                                       'value': 'Department of Physics and Astronomy, University of Oklahoma, Norman, '
                                                'OK, 73019, U.S.A.'}],
                     'email': 'ghk@ou.ed',
                     'full_name': 'Guo, Huai-Ke',
                     'given_names': 'Huai-Ke',
                     'surname': 'Guo'},
                    {'affiliations': [{'country': 'USA',
                                       'organization': 'University of Oklahoma',
                                       'value': 'Department of Physics and Astronomy, University of Oklahoma, Norman, '
                                                'OK, 73019, U.S.A.'}],
                     'email': 'kuver.sinha@ou.ed',
                     'full_name': 'Sinha, Kuver',
                     'given_names': 'Kuver',
                     'surname': 'Sinha'},
                    {'affiliations': [{'country': 'USA',
                                       'organization': 'University of Oklahoma',
                                       'value': 'Department of Physics and Astronomy, University of Oklahoma, Norman, '
                                                'OK, 73019, U.S.A.'}],
                     'email': 'Daniel.d.vagie-1@ou.ed',
                     'full_name': 'Vagie, Daniel',
                     'given_names': 'Daniel',
                     'surname': 'Vagie'}],
        'collections': [{'primary': 'Journal of High Energy Physics'}],
        'control_number': '46684',
        'copyright': [{'holder': 'The Author(s)',
                       'year': '2019'}],
        'dois': [{'value': '10.1007/JHEP04(2019)052'}],
        'imprints': [{'date': '2019-04-05', 'publisher': 'Springer'}],
        'license': [{'license': 'CC-BY-3.0',
                     'url': 'https://creativecommons.org/licenses/by/3.0'}],
        'page_nr': [40],
        'publication_info': [{'artid': 'JHEP042019052',
                              'journal_issue': '4',
                              'journal_title': 'Journal of High Energy Physics',
                              'journal_volume': '2019',
                              'material': 'article',
                              'page_end': '40',
                              'page_start': '1',
                              'year': 2019}],
        'record_creation_date': '2019-04-08T14:30:41.101725',
        'titles': [{'source': 'Springer',
                    'title': 'Collider and gravitational wave complementarity in exploring the [...]'}]
    }

    run_validate(data)


def test_no_doi():
    data = {}
    assert get_first_doi(MockObj(data)) is None


def test_doi():
    data = {'dois': [{'value': '10.1103/PhysRevD.99.045009'}]}
    assert get_first_doi(MockObj(data)) == '10.1103/PhysRevD.99.045009'


def test_orcid():
    data = {'authors': [{'orcid': '1234-1234-1234-1234'}]}
    remove_orcid_prefix(MockObj(data), None)
    assert data == {'authors': [{'orcid': '1234-1234-1234-1234'}]}


def test_no_orcid():
    data = {'authors': [{'full_name': 'G. Anthon'}]}
    remove_orcid_prefix(MockObj(data), None)
    assert data == {'authors': [{'full_name': 'G. Anthon'}]}


def test_orcid_with_prefix():
    data = {'authors': [{'orcid': 'ORCID:1234-1234-1234-1234'}]}
    remove_orcid_prefix(MockObj(data), None)
    assert data == {'authors': [{'orcid': '1234-1234-1234-1234'}]}


def test_orcid_with_https_prefix():
    data = {'authors': [{'orcid': 'https://orcid.org/0000-0003-3413-9548'}]}
    remove_orcid_prefix(MockObj(data), None)
    assert data == {'authors': [{'orcid': '0000-0003-3413-9548'}]}
