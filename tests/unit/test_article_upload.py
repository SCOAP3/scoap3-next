import json

from scoap3.modules.compliance.models import Compliance
from scoap3.modules.records.util import create_from_json


def test_article_upload():
    with open('scoap3/data/scoap3demodata_short.json') as source:
        records = json.loads(source.read())
        create_from_json(records, apply_async=False)

    assert(Compliance.query.count() == 1)
