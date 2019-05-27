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
