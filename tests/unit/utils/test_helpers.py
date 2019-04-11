from scoap3.utils.helpers import clean_oup_package_name


def test_abs_path():
    path = '/harvest/oup/2019-03-30_16:30:41_ptep_iss_2019_3.pdf.zip'
    assert clean_oup_package_name(path) == '2019-03-30_16:30:41_ptep_iss_2019_3'


def test_abs_path2():
    path = '/harvest/oup/2019-03-30_16:30:41_ptep_iss_2019_3_archival.zip'
    assert clean_oup_package_name(path) == '2019-03-30_16:30:41_ptep_iss_2019_3'


def test_abs_path3():
    path = '/harvest/oup/2019-03-30_16:30:41_ptep_iss_2019_3.xml.zip'
    assert clean_oup_package_name(path) == '2019-03-30_16:30:41_ptep_iss_2019_3'


def test_rel_path():
    path = 'oup/2019-03-30_16:30:41_ptep_iss_2019_3.pdf.zip'
    assert clean_oup_package_name(path) == '2019-03-30_16:30:41_ptep_iss_2019_3'


def test_rel_path2():
    path = 'oup/2019-03-30_16:30:41_ptep_iss_2019_3_archival.zip'
    assert clean_oup_package_name(path) == '2019-03-30_16:30:41_ptep_iss_2019_3'


def test_rel_path3():
    path = 'oup/2019-03-30_16:30:41_ptep_iss_2019_3.xml.zip'
    assert clean_oup_package_name(path) == '2019-03-30_16:30:41_ptep_iss_2019_3'


def test_only_file():
    path = '2019-03-30_16:30:41_ptep_iss_2019_3.xml.zip'
    assert clean_oup_package_name(path) == '2019-03-30_16:30:41_ptep_iss_2019_3'


def test_empty():
    assert clean_oup_package_name('') == ''


def test_none():
    assert clean_oup_package_name(None) == ''


def test_not_registered():
    path = '/some/path/2019-03-30_16:30:41_ptep_iss_2019_3.magical.extension'
    assert clean_oup_package_name(path) == '2019-03-30_16:30:41_ptep_iss_2019_3.magical.extension'
