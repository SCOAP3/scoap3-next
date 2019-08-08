import json
from urllib import quote

from inspire_utils.record import get_value
from invenio_search import current_search_client


def test_year_field(app_client, test_record):
    assert test_record['record_creation_date'] == '2019-02-21T14:38:42.640699'
    assert 'year' not in test_record

    doi = get_value(test_record, 'dois[0].value')
    search_param = '"%s"' % doi

    response = app_client.get('/api/records/?q=%s' % quote(search_param))
    data = json.loads(response.data)

    record = data['hits']['hits'][0]['metadata']
    assert 'year' in record
    assert record['year'] == record['imprints'][0]['date'][:4]


def test_api_case_insensitive_doi(app_client, test_record):
    doi = get_value(test_record, 'dois[0].value')

    # has to be non-uppercase doi for the test
    assert doi != doi.upper()

    response_original = app_client.get('/api/records/?q=%s' % quote('"%s"' % doi))
    response_upper = app_client.get('/api/records/?q=%s' % quote('"%s"' % doi.upper()))

    data_original = json.loads(response_original.data)
    data_upper = json.loads(response_upper.data)

    assert data_original['hits'] == data_upper['hits']


def test_case_insensitive_doi(test_record):
    index = 'scoap3-records-record'
    doi = get_value(test_record, 'dois[0].value')
    doi_upper = doi.upper()

    # has to be non-uppercase doi for the test
    assert doi != doi_upper

    data_original = current_search_client.search(body={'query': {'term': {'doi': doi}}}, index=index)
    data_upper = current_search_client.search(body={'query': {'term': {'doi': doi_upper}}}, index=index)

    assert data_original['hits']
    assert data_original['hits'] == data_upper['hits']


def test_source_field(app_client, test_record):
    doi = get_value(test_record, 'dois[0].value')
    search_param = '"%s"' % doi

    response = app_client.get('/api/records/?q=%s&_source=dois' % quote(search_param))
    assert response.status_code == 200
    data = json.loads(response.data)
    results = data['hits']['hits']

    assert len(results) == 1
    result_metadata = results[0]['metadata']
    assert set(result_metadata.keys()) == {'dois', 'control_number'}
    assert result_metadata['dois'][0]['value'] == doi


def test_export(app_client, test_record):
    doi = get_value(test_record, 'dois[0].value')
    search_param = '"%s"' % doi

    response = app_client.get('/search/export?q=%s' % quote(search_param))
    assert response.status_code == 200

    year = test_record['imprints'][0]['date'][:4]
    control_number = test_record['control_number']
    title = get_value(test_record, 'titles[0].title')
    arxiv = ''
    arxiv_categories = ''
    pub_date = get_value(test_record, 'imprints[0].date')
    rec_create = test_record['record_creation_date']
    publisher = get_value(test_record, 'publication_info[0].journal_title')
    expected_data = ('"Publication year";"Control number";"DOI";"Title";"arXiv id";"arXiv primary category";"Publicatio'
                     'n date";"Record creation date";"Publisher"\r\n"%s";"%s";"%s";"%s";"%s";"%s";"%s";"%s";"%s"'
                     '\r\n' % (
                         year, control_number, doi, title, arxiv, arxiv_categories, pub_date, rec_create, publisher)
                     )

    assert response.data.decode('utf8') == expected_data


def test_export_source(app_client, test_record):
    doi = get_value(test_record, 'dois[0].value')
    search_param = '"%s"' % doi

    response = app_client.get('/search/export?q=%s&_source=year' % quote(search_param))
    assert response.status_code == 200

    year = test_record['imprints'][0]['date'][:4]
    control_number = test_record['control_number']
    expected_data = '"Publication year";"Control number"\r\n"%s";"%s"\r\n' % (year, control_number)

    assert response.data == expected_data
