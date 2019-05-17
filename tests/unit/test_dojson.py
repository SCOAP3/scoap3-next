import json
from os import path

import pytest

from scoap3.dojson.dump_utils import dumps_etree
from scoap3.dojson.hep import hep2marc
from tests.responses import get_response_dir

namespaces = {'m': 'http://www.loc.gov/MARC21/slim'}


def get_subfield(xml, field_tag, subfield_code):
    return xml.xpath('./m:datafield[@tag="%s"]/m:subfield[@code="%s"]/text()' % (field_tag, subfield_code),
                     namespaces=namespaces)


@pytest.fixture
def xml():
    file_path = path.join(get_response_dir(), 'scoap3', 'aps_record.json')
    with open(file_path, 'rt') as f:
        record = json.loads(f.read())
        return dumps_etree(hep2marc.do(record))


def test_field_540(xml):
    assert get_subfield(xml, '540', 'a') == ['CC-BY-4.0']
    assert get_subfield(xml, '540', 'u') == ['https://creativecommons.org/licenses/by/4.0/']


def test_field_300(xml):
    assert get_subfield(xml, '300', 'a') == ['8']


def test_field_541(xml):
    assert get_subfield(xml, '541', 'a') == ['APS']
    assert get_subfield(xml, '541', 'c') == ['APS']
    assert get_subfield(xml, '541', 'e') == ['54456c823c8211e9aa3402163e01809a']
    assert get_subfield(xml, '541', 'd') == ['2019-03-02T01:30:20.220971']


def test_field_100(xml):
    assert get_subfield(xml, '100', 'a') == ['Sarma, Pranjal',
                                             'Bhattacharjee, Buddhadeb']
    assert get_subfield(xml, '100', 'u') == ['Nuclear and Radiation Physics Research Laboratory, Department of Physics,'
                                             ' Gauhati University, Guwahati, Assam - 781014, India',
                                             'Nuclear and Radiation Physics Research Laboratory, Department of Physics,'
                                             ' Gauhati University, Guwahati, Assam - 781014, India']


def test_field_245(xml):
    assert get_subfield(xml, '245', 'a') == ['Color reconnection as a possible mechanism of intermittency in the emissi'
                                             'on spectra of charged particles in PYTHIA-generated high-multiplicity <m'
                                             'ath><mrow><mi>p</mi><mi>p</mi></mrow></math> collisions at energies avai'
                                             'lable at the CERN Large Hadron Collider']
    assert get_subfield(xml, '245', '9') == ['APS']


def test_field_980(xml):
    assert get_subfield(xml, '980', 'a') == ['HEP', 'Citeable', 'Published']


def test_field_024(xml):
    assert get_subfield(xml, '024', 'a') == ['10.1103/PhysRevC.99.034901']
    assert get_subfield(xml, '024', '2') == ['DOI']


def test_field_037(xml):
    assert get_subfield(xml, '037', 'a') == ['1902.09124']
    assert get_subfield(xml, '037', '9') == ['arXiv']
    assert get_subfield(xml, '037', 'c') == ['hep-ph']


def test_field_773(xml):
    assert get_subfield(xml, '773', 'y') == ['2019']
    assert get_subfield(xml, '773', 'p') == ['Physical Review C']
    assert get_subfield(xml, '773', 'v') == ['99']
    assert get_subfield(xml, '773', 'n') == ['3']


def test_field_542(xml):
    assert get_subfield(xml, '542', 'f') == ['Published by the American Physical Society']


def test_field_520(xml):
    assert get_subfield(xml, '520', 'a') == [
        u'Nonstatistical fluctuation in pseudorapidity (<math><mi>\u03b7</mi></math>), azimuthal (<math><mi>\u03d5</mi>'
        u'</math>), and pseudorapidity-azimuthal (<math><mrow><mi>\u03b7</mi><mtext>\u2013</mtext><mi>\u03d5</mi></mrow'
        u'></math>) distribution spectra of primary particles of PYTHIA Monash (default) generated <math><mrow><mi>p</m'
        u'i><mi>p</mi></mrow></math> events at <math><mrow><msqrt><mi>s</mi></msqrt><mo>=</mo><mn>2.76</mn></mrow></mat'
        u'h>, 7, and 13 TeV have been studied using the scaled factorial moment technique. A weak intermittent type of '
        u'emission could be realized for minimum-bias (MB) <math><mrow><mi>p</mi><mi>p</mi></mrow></math> events in <ma'
        u'th><mrow><mi>\u03c7</mi><mo>(</mo><mi>\u03b7</mi><mtext>\u2013</mtext><mi>\u03d5</mi><mo>)</mo></mrow></math>'
        u' space and a much stronger intermittency could be observed in high-multiplicity (HM) <math><mrow><mi>p</mi><'
        u'mi>p</mi></mrow></math> events in all <math><mrow><mi>\u03c7</mi><mo>(</mo><mi>\u03b7</mi><mo>)</mo></mrow><'
        u'/math>, <math><mrow><mi>\u03c7</mi><mo>(</mo><mi>\u03d5</mi><mo>)</mo></mrow></math>, and <math><mrow><mi>'
        u'\u03c7</mi><mo>(</mo><mi>\u03b7</mi><mtext>\u2013</mtext><mi>\u03d5</mi><mo>)</mo></mrow></math> spaces at a'
        u'll the studied energies. For HM <math><mrow><mi>p</mi><mi>p</mi></mrow></math> events, at a particular energy'
        u', the intermittency index <math><msub><mi>\u03b1</mi><mi>q</mi></msub></math> is found to be largest in two-d'
        u'imensional <math><mrow><mi>\u03c7</mi><mo>(</mo><mi>\u03b7</mi><mtext>\u2013</mtext><mi>\u03d5</mi><mo>)</mo>'
        u'</mrow></math> space and least in <math><mrow><mi>\u03c7</mi><mo>(</mo><mi>\u03b7</mi><mo>)</mo></mrow></math'
        u'> space, and no center of mass energy dependence of <math><msub><mi>\u03b1</mi><mi>q</mi></msub></math> could'
        u' be observed. The anomalous dimensions <math><msub><mi>d</mi><mi>q</mi></msub></math> are observed to be incr'
        u'eased with the order of the moment <math><mi>q</mi></math>, suggesting a multifractal nature of the emission '
        u'spectra of various studied events. While, the coefficient <math><msub><mi>\u03bb</mi><mi>q</mi></msub></math>'
        u' is found to decrease monotonically with the order of the moment <math><mi>q</mi></math> for two-dimensional '
        u'analysis of MB <math><mrow><mi>p</mi><mi>p</mi></mrow></math> events as well as for one-dimensional analysis '
        u'of HM <math><mrow><mi>p</mi><mi>p</mi></mrow></math> events, a clear minimum in <math><msub><mi>\u03bb</mi><m'
        u'i>q</mi></msub></math> values could be observed from the two-dimensional HM <math><mrow><mi>p</mi><mi>p</mi><'
        u'/mrow></math> data analysis. For PYTHIA Monash generated sets of data, the strength of the intermittency is f'
        u'ound to vary significantly with the variation of the strength of the color reconnection (CR) parameter, i.e.,'
        u' reconnection range RR, for <math><mrow><mi>RR</mi><mo>=</mo><mn>0.0</mn></mrow></math>, 1.8 and 3.0, thereby'
        u', establishing a strong connection between the CR mechanism and the observed intermittent type of emission of'
        u' primary charged particles of the studied high-multiplicity <math><mrow><mi>p</mi><mi>p</mi></mrow></math>'
        u' events.'
    ]
    assert get_subfield(xml, '520', '9') == ['APS']


def test_field_260(xml):
    assert get_subfield(xml, '260', 'c') == ['2019-03-01']
    assert get_subfield(xml, '260', 'b') == ['APS']
