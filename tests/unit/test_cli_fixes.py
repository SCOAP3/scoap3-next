from scoap3.cli_fixes import utf8rec, validate_utf8


class MockRecord:
    id = None

    def __init__(self, json):
        self.json = json


def test_utf8_fix_22934_source():
    data = u'Springer/Societ\u00c3\u00a0 Italiana di Fisica'
    expected = u'Springer/Societ\xe0 Italiana di Fisica'
    assert validate_utf8(data) == (1, 0)
    assert utf8rec(data, MockRecord({})) == expected


def test_utf8_fix_22934_title():
    data = u'Status and prospects of light bino\u00e2\u0080\u0093higgsino dark matter in natural SUSY'
    expected = u'Status and prospects of light bino\u2013higgsino dark matter in natural SUSY'
    assert validate_utf8(data) == (1, 0)
    assert utf8rec(data, MockRecord({})) == expected


def test_utf8_fix_18162_abstract():
    data = u'On the other hand, LHC results for pp\u00e2\u0086\u0092e+ missing'
    expected = u'On the other hand, LHC results for pp\u2192e+ missing'
    assert validate_utf8(data) == (1, 0)
    assert utf8rec(data, MockRecord({})) == expected


def test_utf8_fix_18162_abstract_double():
    data = u'On the other hand, LHC results for pp\u00e2\u0086\u0092e+ missing'
    converted = utf8rec(data, MockRecord({}))
    assert validate_utf8(converted) == (0, 1)


def test_utf8_fix_18100_title_removed_bad():
    data = u'Search for new resonances decaying to a W or Z boson and a Higgs boson in the ' \
           u'\u00e2\u0084\u0093+\u00e2\u0084\u0093\u00e2\u0088\u0092bb\u00c2\u00af , \u00e2\u0084\u0093\u00ce\u00bdbb' \
           u'\u00c2\u00af , and \u00ce\u00bd\u00ce\u00bd\u00c2\u00afbb\u00c2\u00af channels with pp collisions at' \
           u' s=13 TeV with the ATLAS detector'
    expected = u'Search for new resonances decaying to a W or Z boson and a Higgs boson in the \u2113+\u2113\u2212bb' \
               u'\xaf , \u2113\u03bdbb\xaf , and \u03bd\u03bd\xafbb\xaf channels with pp collisions at s=13 TeV with ' \
               u'the ATLAS detector'
    assert validate_utf8(data) == (11, 0)
    assert utf8rec(data, MockRecord({})) == expected


def test_utf8_fix_18100_expected_validate():
    expected = u'Search for new resonances decaying to a W or Z boson and a Higgs boson in the \u2113+\u2113\u2212bb' \
               u'\xaf , \u2113\u03bdbb\xaf , and \u03bd\u03bd\xafbb\xaf channels with pp collisions at s=13 TeV with ' \
               u'the ATLAS detector'
    assert validate_utf8(expected) == (0, 11)


def test_utf8_fix_18100_title():
    data = u'Search for new resonances decaying to a W or Z boson and a Higgs boson in the \u00e2\u0084\u0093+' \
           u'\u00e2\u0084\u0093\u00e2\u0088\u0092bb\u00c2\u00af , \u00e2\u0084\u0093\u00ce\u00bdbb\u00c2\u00af , and ' \
           u'\u00ce\u00bd\u00ce\u00bd\u00c2\u00afbb\u00c2\u00af channels with pp collisions at s=13\u00c2 TeV with the ' \
           u'ATLAS detector'
    assert validate_utf8(data) == (11, 1)
