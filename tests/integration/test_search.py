import json
from urllib import quote

from inspire_utils.record import get_value


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


def test_case_insensitive_doi(app_client, test_record):
    doi = get_value(test_record, 'dois[0].value')

    # has to be non-uppercase doi for the test
    assert doi != doi.upper()

    response_original = app_client.get('/api/records/?q=%s' % quote('"%s"' % doi))
    response_upper = app_client.get('/api/records/?q=%s' % quote('"%s"' % doi.upper()))

    data_original = json.loads(response_original.data)
    data_upper = json.loads(response_upper.data)

    assert data_original['hits'] == data_upper['hits']
