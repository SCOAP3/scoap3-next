
from invenio_search import current_search_client as es
from inspire_utils.record import get_value

def find_hindawi_missing_files():
    records = {}

    dois = ["10.1155/2022/4299254",
    "10.1155/2022/7710817",
    "10.1155/2022/7475923",
    "10.1155/2022/7274958",
    "10.1155/2022/5511428",
    "10.1155/2022/3136459",
    "10.1155/2022/5287693",
    "10.1155/2022/8970837",
    "10.1155/2022/7396078"
    ]

    for doi in dois:
        query = {
            "query": {
                "bool": {
                    "must": [{"match": {"metadata.dois.value": doi}}],
                }
            }
        }

        page = es.search(index="scoap3-workflows-harvesting", scroll='1m', body=query)
        sid = page['_scroll_id']
        scroll_size = len(page['hits']['hits'])
        while (scroll_size > 0):
            for record_index in range(scroll_size):
                status = get_value(page["hits"]["hits"][record_index], "_source._workflow.status" , "None")
                name = doi + str(record_index)
                records[name] = status
            page = es.scroll(scroll_id=sid, scroll='2m')
            sid = page['_scroll_id']
            scroll_size = len(page['hits']['hits'])

    return records