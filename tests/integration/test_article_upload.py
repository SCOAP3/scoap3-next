import json
import re
from os import path

import requests_mock
from invenio_pidstore.models import PersistentIdentifier
from invenio_records import Record
from invenio_workflows import Workflow
from mock import patch
from workflow.engine_db import WorkflowStatus
from workflow.errors import HaltProcessing

from scoap3.modules.records.util import create_from_json
from tests.responses import get_response_dir, read_hep_schema, read_titles_schema, read_response


def _get_record_from_workflow(workflow):
    assert len(workflow.objects) == 1
    workflow_object = workflow.objects[0]

    recid = workflow_object.data['control_number']
    pid = PersistentIdentifier.get('recid', recid)

    return Record.get_record(pid.object_uuid)


def mock_halt(msg, obj, eng):
    raise HaltProcessing(msg)


def run_workflow(input_json_filename, mock_address):
    """Use input_json_filename to load hepcrawl response and to run article_upload workflow."""

    file_path = path.join(get_response_dir(), 'hepcrawl', input_json_filename)
    with open(file_path, 'rt') as f:
        json_data = json.loads(f.read())

    with patch('scoap3.modules.workflows.workflows.articles_upload.__halt_and_notify', mock_halt):
        mock_address.register_uri('GET', '/schemas/hep.json', content=read_hep_schema())
        mock_address.register_uri('GET', '/schemas/elements/titles.json', content=read_titles_schema())
        mock_address.register_uri(
            requests_mock.ANY,
            re.compile('.*(indexer).*'),
            real_http=True,
        )
        workflow_id = create_from_json({'records': [json_data]}, apply_async=False)[0]

    return Workflow.query.get(workflow_id)


def test_hindawi():
    workflows_count = Workflow.query.count()

    with requests_mock.Mocker() as m:
        m.get('http://downloads.hindawi.com/journals/ahep/2019/4123108.pdf',
              content=read_response('article_upload', 'hindawi.com_journals_ahep_2019_4123108.pdf'))
        m.get('http://downloads.hindawi.com/journals/ahep/2019/4123108.xml',
              content=read_response('article_upload', 'hindawi.com_journals_ahep_2019_4123108.xml'))
        m.get('https://api.crossref.org/works/10.1155/2019/4123108',
              content=read_response('article_upload', 'crossref.org_works_10.1155_2019_4123108'))
        workflow = run_workflow('hindawi.json', m)

    assert workflow.status == WorkflowStatus.COMPLETED
    assert Workflow.query.count() - workflows_count == 1

    record = _get_record_from_workflow(workflow)
    assert len(record['_files']) == 2
    assert record['_oai']['sets'] == ['AHEP']
    assert record['abstracts'][0]['value'] == ''
    assert record['acquisition_source']['method'] == 'Hindawi'

    assert record['authors'] == [
        {'affiliations': [{'country': 'Greece',
                           'value': 'Division of Theoretical Physics, University of Ioannina, '
                                    'GR-45110 Ioannina, Greece'}],
         'full_name': 'Kosmas, Theocharis',
         'given_names': 'Theocharis',
         'orcid': '0000-0001-6245-6589',
         'raw_name': 'Kosmas, Theocharis',
         'surname': 'Kosmas'},
        {'affiliations': [{'country': 'Japan',
                           'value': 'Research Center for Nuclear Physics, Osaka University, '
                                    'Ibaraki Osaka 567-0047, Japan'}],
         'full_name': 'Ejiri, Hiroyasu',
         'given_names': 'Hiroyasu',
         'orcid': '0000-0003-0568-3528',
         'raw_name': 'Ejiri, Hiroyasu',
         'surname': 'Ejiri'},
        {'affiliations': [{'country': 'USA',
                           'value': 'Physics Department, University of Tennessee, Knoxville, TN, USA'}],
         'full_name': 'Hatzikoutelis, Athanasios',
         'given_names': 'Athanasios',
         'orcid': '0000-0001-5405-1485',
         'raw_name': 'Hatzikoutelis, Athanasios',
         'surname': 'Hatzikoutelis'}
    ]
    assert record['collections'] == [{'primary': 'Advances in High Energy Physics'}]
    assert record['copyright'] == [{'holder': '', 'material': '',
                                    'statement': u'Copyright \xa9 2019 Theocharis Kosmas et al.', 'year': '2019'}]
    assert record['dois'] == [{'value': '10.1155/2019/4123108'}]
    assert record['imprints'] == [{'date': '2019-02-17', 'publisher': 'Hindawi'}]
    assert record['license'] == [{'license': 'CC-BY-3.0', 'url': 'http://creativecommons.org/licenses/by/3.0/'}]
    assert record['page_nr'] == [3]
    assert record['publication_info'] == [{'artid': '',
                                           'journal_issue': '',
                                           'journal_title': 'Advances in High Energy Physics',
                                           'journal_volume': '',
                                           'material': '',
                                           'page_end': '',
                                           'page_start': '4123108',
                                           'pubinfo_freetext': '',
                                           'year': 2019}]
    assert record['titles'][0]['title'] == 'Neutrino Physics in the Frontiers of Intensities and Very ' \
                                           'High Sensitivities 2018'


def test_aps():
    workflows_count = Workflow.query.count()

    with requests_mock.Mocker() as m:
        m.get('http://export.arxiv.org/api/query?search_query=id:1811.06024',
              content=read_response('article_upload', 'export.arxiv.org_api_query_search_query_id_1811.06024'))
        m.register_uri('GET', 'http://harvest.aps.org/v2/journals/articles/10.1103/PhysRevD.99.045009',
                       request_headers={'Accept': 'application/pdf'},
                       content=read_response('article_upload', 'harvest.aps.org_PhysRevD.99.045009.pdf'))
        m.register_uri('GET', 'http://harvest.aps.org/v2/journals/articles/10.1103/PhysRevD.99.045009',
                       request_headers={'Accept': 'text/xml'},
                       content=read_response('article_upload', 'harvest.aps.org_PhysRevD.99.045009.xml'))
        m.get('https://api.crossref.org/works/10.1103/PhysRevD.99.045009',
              content=read_response('article_upload', 'crossref.org_works_10.1103_PhysRevD.99.045009'))
        workflow = run_workflow('aps.json', m)

    assert workflow.status == WorkflowStatus.COMPLETED
    assert Workflow.query.count() - workflows_count == 1

    record = _get_record_from_workflow(workflow)
    assert len(record['_files']) == 2
    assert record['_oai']['sets'] == ['PRD']
    assert record['abstracts'][0]['value'] == (
        'We obtain novel factorization identities for nonlinear sigma model amplitudes using a new integrand in the Ca'
        'chazo-He-Yuan double-cover prescription. We find that it is possible to write very compact relations using on'
        'ly longitudinal degrees of freedom. We discuss implications for on shell recursion.')
    assert record['acquisition_source']['method'] == 'APS'
    assert record['arxiv_eprints'] == [{'categories': ['hep-th'], 'value': '1811.06024'}]
    assert record['authors'] == [
        {'affiliations': [{'country': 'Denmark',
                           'value': u'Niels Bohr International Academy and Discovery Center Niels Bohr Insitute, '
                                    u'University of Copenhagen Blegdamsvej 17, DK-2100 Copenhagen \xd8, Denmark'}],
         'full_name': u'Bjerrum-Bohr, N.\u2009E.\u2009J.',
         'given_names': u'N.\u2009E.\u2009J.',
         'raw_name': u'N.\u2009E.\u2009J. Bjerrum-Bohr',
         'surname': 'Bjerrum-Bohr'},
        {'affiliations': [{'country': 'Denmark',
                           'value': u'Niels Bohr International Academy and Discovery Center Niels Bohr Insitute, '
                                    u'University of Copenhagen Blegdamsvej 17, DK-2100 Copenhagen \xd8, Denmark'},
                          {'country': 'Colombia',
                           'value': u'Facultad de Ciencias, Basicas Universidad Santiago de Cali, Calle 5 N\xb0 62-00 '
                                    u'Barrio Pampalinda Cali, Valle, Colombia'}],
         'full_name': 'Gomez, Humberto',
         'given_names': 'Humberto',
         'raw_name': 'Humberto Gomez',
         'surname': 'Gomez'},
        {'affiliations': [{'country': 'Denmark',
                           'value': u'Niels Bohr International Academy and Discovery Center Niels Bohr Insitute, '
                                    u'University of Copenhagen Blegdamsvej 17, DK-2100 Copenhagen \xd8, Denmark'}],
         'full_name': 'Helset, Andreas',
         'given_names': 'Andreas',
         'raw_name': 'Andreas Helset',
         'surname': 'Helset'}
    ]
    assert record['collections'] == [{'primary': 'HEP'}, {'primary': 'Citeable'}, {'primary': 'Published'}]
    assert record['copyright'] == [{'holder': '', 'material': '',
                                    'statement': 'Published by the American Physical Society', 'year': '2019'}]
    assert record['dois'] == [{'value': '10.1103/PhysRevD.99.045009'}]
    assert record['imprints'] == [{'date': '2019-02-19', 'publisher': 'APS'}]
    assert record['license'] == [{'license': 'CC-BY-4.0', 'url': 'https://creativecommons.org/licenses/by/4.0/'}]
    assert record['page_nr'] == [6]
    assert record['publication_info'] == [{'artid': '',
                                           'journal_issue': '4',
                                           'journal_title': 'Physical Review D',
                                           'journal_volume': '99',
                                           'material': 'article',
                                           'page_end': '',
                                           'page_start': '',
                                           'pubinfo_freetext': '',
                                           'year': 2019}]
    assert record['titles'][0]['title'] == 'New factorization relations for nonlinear sigma model amplitudes'


def test_elsevier():
    workflows_count = Workflow.query.count()

    with requests_mock.Mocker() as m:
        m.get('https://api.crossref.org/works/10.1016/j.nuclphysb.2018.07.004',
              content=read_response('article_upload', 'crossref.org_works_10.1016_j.nuclphysb.2018.07.004'))
        workflow = run_workflow('elsevier/elsevier.json', m)

    assert workflow.status == WorkflowStatus.COMPLETED
    assert Workflow.query.count() - workflows_count == 1

    record = _get_record_from_workflow(workflow)
    assert len(record['_files']) == 2
    assert record['_oai']['sets'] == ['NPB']
    assert record['abstracts'][0]['value'] == (
        'Renormalization plays an important role in the theoretically and mathematically careful analysis of models in '
        'condensed-matter physics. I review selected results about correlated-fermion systems, ranging from mathematica'
        'l theorems to applications in models relevant for materials science, such as the prediction of equilibrium pha'
        'ses of systems with competing ordering tendencies, and quantum criticality.')
    assert record['acquisition_source']['method'] == 'Elsevier'
    assert record['authors'] == [{'affiliations': [{'country': 'Germany',
                                                    'value': u'Institut f\xfcr Theoretische Physik, Universit\xe4t Heid'
                                                             u'elberg, Philosophenweg 19, 69120 Heidelberg, Germany'}],
                                  'email': 'salmhofer@uni-heidelberg.de',
                                  'full_name': 'Salmhofer, Manfred',
                                  'given_names': 'Manfred',
                                  'surname': 'Salmhofer'}]
    assert record['collections'] == [{u'primary': u'Nuclear Physics B'}]
    assert record['copyright'] == [{'holder': 'The Author', 'material': '', 'statement': 'The Author', 'year': '2018'}]
    assert record['dois'] == [{'value': '10.1016/j.nuclphysb.2018.07.004'}]
    assert record['imprints'] == [{'date': '2018-07-04', 'publisher': 'Elsevier'}]
    assert record['license'] == [{'license': 'CC-BY-3.0', 'url': 'http://creativecommons.org/licenses/by/3.0/'}]
    assert record['publication_info'] == [{'artid': '14394',
                                           'journal_issue': '',
                                           'journal_title': 'Nuclear Physics B',
                                           'journal_volume': '',
                                           'material': 'article',
                                           'page_end': '',
                                           'page_start': '',
                                           'pubinfo_freetext': '',
                                           'year': 2018}]
    assert record['titles'][0]['title'] == u'Renormalization in condensed matter: Fermionic systems \u2013 ' \
                                           u'from mathematics to materials'


def test_springer():
    workflows_count = Workflow.query.count()

    with requests_mock.Mocker() as m:
        m.get('http://export.arxiv.org/api/query?search_query=id:1810.09837',
              content=read_response('article_upload', 'export.arxiv.org_api_query_search_query_id:1810.09837'))
        m.get('https://api.crossref.org/works/10.1140/epjc/s10052-019-6572-3',
              content=read_response('article_upload', 'crossref.org_works_10.1140_epjc_s10052-019-6572-3'))
        workflow = run_workflow('springer/springer.json', m)

    assert workflow.status == WorkflowStatus.COMPLETED
    assert Workflow.query.count() - workflows_count == 1

    record = _get_record_from_workflow(workflow)
    assert len(record['_files']) == 2
    assert record['_oai']['sets'] == ['EPJC']
    assert record['abstracts'][0]['value'] == (
        'We discuss in detail the distributions of energy, radial pressure and tangential pressure inside the nucleon. '
        'In particular, this discussion is carried on in both the instant form and the front form of dynamics. Moreover'
        ' we show for the first time how these mechanical concepts can be defined when the average nucleon momentum doe'
        's not vanish. We express the conditions of hydrostatic equilibrium and stability in terms of these two and thr'
        'ee-dimensional energy and pressure distributions. We briefly discuss the phenomenological relevance of our fin'
        'dings with a simple yet realistic model. In the light of this exhaustive mechanical description of the nucleon'
        ', we also present several possible connections between hadronic physics and compact stars, like e.g. the study'
        ' of the equation of state for matter under extreme conditions and stability constraints.')
    assert record['acquisition_source']['method'] == 'Springer'
    assert record['arxiv_eprints'] == [{'categories': ['hep-ph'], 'value': '1810.09837'}]
    assert record['authors'] == [
        {'affiliations': [{'country': 'France',
                           'organization': u'Universit\xe9 Paris-Saclay',
                           'value': u'Centre de Physique Th\xe9orique, \xc9cole polytechnique, CNRS, Universit\xe9 '
                                    u'Paris-Saclay, Palaiseau, 91128, France'}],
         'full_name': u'Lorc\xe9, C\xe9dric',
         'given_names': u'C\xe9dric',
         'surname': u'Lorc\xe9'},
        {'affiliations': [{'country': 'France',
                           'organization': u'Universit\xe9 Paris-Saclay',
                           'value': u'IRFU, CEA, Universit\xe9 Paris-Saclay, Gif-sur-Yvette, 91191, France'}],
         'full_name': u'Moutarde, Herv\xe9',
         'given_names': u'Herv\xe9',
         'surname': 'Moutarde'},
        {'affiliations': [{'country': 'France',
                           'organization': u'Universit\xe9 Paris-Saclay',
                           'value': u'Centre de Physique Th\xe9orique, \xc9cole polytechnique, CNRS, Universit\xe9 '
                                    u'Paris-Saclay, Palaiseau, 91128, France'},
                          {'country': 'France',
                           'organization': u'Universit\xe9 Paris-Saclay',
                           'value': u'IRFU, CEA, Universit\xe9 Paris-Saclay, Gif-sur-Yvette, 91191, France'}],
         'email': 'Arkadiusz.Trawinski@cea.fr',
         'full_name': u'Trawi\u0144ski, Arkadiusz',
         'given_names': 'Arkadiusz',
         'surname': u'Trawi\u0144ski'}
    ]
    assert record['collections'] == [{'primary': 'European Physical Journal C'}]
    assert record['copyright'] == [{'holder': 'The Author(s)', 'material': '',
                                    'statement': '', 'year': '2019'}]
    assert record['dois'] == [{'value': '10.1140/epjc/s10052-019-6572-3'}]
    assert record['imprints'] == [{'date': '2019-01-29', 'publisher': 'Springer'}]
    assert record['license'] == [{'license': 'CC-BY-4.0', 'url': 'https://creativecommons.org/licenses//by/4.0'}]
    assert record['page_nr'] == [25]
    assert record['publication_info'] == [{'artid': 's10052-019-6572-3',
                                           'journal_issue': '1',
                                           'journal_title': 'European Physical Journal C',
                                           'journal_volume': '79',
                                           'material': 'article',
                                           'page_end': '25',
                                           'page_start': '1',
                                           'pubinfo_freetext': '',
                                           'year': 2019}]
    assert record['titles'][0]['title'] == 'Revisiting the mechanical properties of the nucleon'


def test_oup():
    workflows_count = Workflow.query.count()

    with requests_mock.Mocker() as m:
        m.get('http://export.arxiv.org/api/query?search_query=id:1611.10151',
              content=read_response('article_upload', 'export.arxiv.org_api_query_search_query_id:1611.10151'))
        m.get('https://api.crossref.org/works/10.1093/ptep/pty143',
              content=read_response('article_upload', 'crossref.org_works_10.1093_ptep_pty143'))
        workflow = run_workflow('oup/oup.json', m)

    assert workflow.status == WorkflowStatus.COMPLETED
    assert Workflow.query.count() - workflows_count == 1

    record = _get_record_from_workflow(workflow)
    assert len(record['_files']) == 3
    assert record['_oai']['sets'] == ['PTEP']
    assert record['abstracts'][0]['value'] == (
        u'Abstract Regarding the significant interests in massive gravity and combining it with gravity\u2019s rainbow '
        u'and also BTZ black holes, we apply the formalism introduced by Jiang and Han in order to investigate the quan'
        u'tization of the entropy of black holes. We show that the entropy of BTZ black holes in massive gravity\u2019s '
        u'rainbow is quantized with equally spaced spectra and it depends on the black holes\u2019 properties including '
        u'massive parameters, electrical charge, the cosmological constant, and also rainbow functions. In addition, we '
        u'show that quantization of the entropy results in the appearance of novel properties for this quantity, such as'
        u' the existence of divergences, non-zero entropy in a vanishing horizon radius, and the possibility of tracing '
        u'out the effects of the black holes\u2019 properties. Such properties are absent in the non-quantized version o'
        u'f the black hole entropy. Furthermore, we investigate the effects of quantization on the thermodynamical behav'
        u'ior of the solutions. We confirm that due to quantization, novel phase transition points are introduced and st'
        u'able solutions are limited to only de Sitter black holes (anti-de Sitter and asymptotically flat solutions are'
        u' unstable).')
    assert record['acquisition_source']['method'] == 'OUP'
    assert record['arxiv_eprints'] == [{'categories': ['hep-th', 'gr-qc'], 'value': '1611.10151'}]
    assert record['authors'] == [
        {'affiliations': [{'country': 'Iran',
                           'value': 'Physics Department and Biruni Observatory, College of Sciences, Shiraz University,'
                                    ' Shiraz 71454, Iran'}],
         'email': 'beslampanah@shirazu.ac.ir',
         'full_name': 'Panah, B Eslam',
         'given_names': 'B Eslam',
         'surname': 'Panah'},
        {'affiliations': [{'country': 'Germany',
                           'value': u'Helmholtz-Institut Jena, Fr\xf6belstieg 3, Jena D-07743 Germany'}],
         'full_name': 'Panahiyan, S',
         'given_names': 'S',
         'surname': 'Panahiyan'},
        {'affiliations': [{'country': 'Iran',
                           'value': 'Physics Department and Biruni Observatory, College of Sciences, Shiraz University,'
                                    ' Shiraz 71454, Iran'}],
         'full_name': 'Hendi, S H',
         'given_names': 'S H',
         'surname': 'Hendi'}
    ]
    assert record['collections'] == [{'primary': 'Progress of Theoretical and Experimental Physics'}]
    assert record['copyright'] == [{'holder': '', 'material': '',
                                    'statement': u'\xa9  The Author(s) 2019. Published by Oxford University Press on '
                                                 'behalf of the Physical Society of Japan.',
                                    'year': '2019'}]
    assert record['dois'] == [{'value': '10.1093/ptep/pty143'}]
    assert record['imprints'] == [{'date': '2019-01-17', 'publisher': 'OUP'}]
    assert record['license'] == [{'license': 'CC-BY-4.0', 'url': 'http://creativecommons.org/licenses/by/4.0/'}]
    assert record['page_nr'] == [13]
    assert record['publication_info'] == [{'artid': '013E02',
                                           'journal_issue': '1',
                                           'journal_title': 'Progress of Theoretical and Experimental Physics',
                                           'journal_volume': '2019',
                                           'material': 'article',
                                           'page_end': '',
                                           'page_start': '',
                                           'pubinfo_freetext': '',
                                           'year': 2019}]
    assert record['titles'][0]['title'] == u'Entropy spectrum of charged BTZ black holes in' \
                                           u' massive gravity\u2019s rainbow'
