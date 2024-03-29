# -*- coding: utf-8 -*-
from flask import current_app
from lxml import etree


namespaces = {'m': 'http://www.loc.gov/MARC21/slim',
              'o': 'http://www.openarchives.org/OAI/2.0/'}


def get_control_field(xml, field_tag):
    return xml.xpath('./o:controlfield[@tag="%s"]/text()' % field_tag, namespaces=namespaces)


def get_subfield(xml, field_tag, subfield_code):
    return xml.xpath('./o:datafield[@tag="%s"]/o:subfield[@code="%s"]/text()' % (field_tag, subfield_code),
                     namespaces=namespaces)


def test_record_by_id(app_client, test_record):
    assert 'control_number' in test_record
    control_number = test_record['control_number']

    assert 'id' in test_record.get('_oai', {})
    identifier = test_record['_oai']['id']

    response = app_client.get('/oai2d?verb=GetRecord&metadataPrefix=marc21&identifier=%s' % identifier)

    xml = etree.fromstring(response.data).find('.//o:metadata/o:record', namespaces=namespaces)
    assert get_control_field(xml, '001') == [control_number]
    assert get_control_field(xml, '005') == ['20190221143842.0']
    assert get_subfield(xml, '100', 'a') == ['Salmhofer, Manfred']
    assert get_subfield(xml, '100', 'u') == [u'Institut für Theoretische Physik, Universität Heidelberg, '
                                             u'Philosophenweg 19, 69120 Heidelberg, Germany']
    assert get_subfield(xml, '245', 'a') == [u'Renormalization in condensed matter: Fermionic systems – '
                                             u'from mathematics to materials']
    assert get_subfield(xml, '245', '9') == ['Elsevier']
    assert get_subfield(xml, '024', 'a') == ['10.1016/j.nuclphysb.2018.07.004']
    assert get_subfield(xml, '024', '2') == ['DOI']
    assert get_subfield(xml, '773', 'y') == ['2018']
    assert get_subfield(xml, '773', 'p') == ['Nuclear Physics B']
    assert get_subfield(xml, '540', 'a') == ['CC-BY-3.0']
    assert get_subfield(xml, '540', 'u') == ['http://creativecommons.org/licenses/by/3.0/']
    assert get_subfield(xml, '542', 'd') == ['The Author']
    assert get_subfield(xml, '542', 'f') == ['The Author']
    assert get_subfield(xml, '520', 'a') == ['Renormalization plays an important role in the theoretically and mathemat'
                                             'ically careful analysis of models in condensed-matter physics. I review s'
                                             'elected results about correlated-fermion systems, ranging from mathematic'
                                             'al theorems to applications in models relevant for materials science, suc'
                                             'h as the prediction of equilibrium phases of systems with competing order'
                                             'ing tendencies, and quantum criticality.']
    assert get_subfield(xml, '520', '9') == ['Elsevier']
    assert get_subfield(xml, '260', 'c') == ['2018-07-04']
    assert get_subfield(xml, '260', 'b') == ['Elsevier']

    files = get_subfield(xml, '856', 'u')
    assert len(files) == 2
    file_xml, file_pdf = files
    servername = current_app.config.get('SERVER_NAME')
    assert file_xml.startswith('http://%s/api/files/' % servername)
    assert file_xml.endswith('/10.1016/j.nuclphysb.2018.07.004.xml')
    assert file_pdf.startswith('http://%s/api/files/' % servername)
    assert file_pdf.endswith('/10.1016/j.nuclphysb.2018.07.004.pdf')

    assert get_subfield(xml, '856', 'y') == ['xml', 'pdf']


def test_not_found(app_client):
    response = app_client.get('/oai2d?verb=GetRecord&metadataPrefix=marc21&identifier=NOT_EXISTING_IDENTIFIER')
    assert response.status_code == 422
