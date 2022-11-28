from invenio_search import current_search_client as es

def get_all_elsevier_records_without_pdfa():
    no_pdfas = {}
    no_files_at_all = {}
    query = {
        "_source": ["_files", "control_number", "dois"],
        "query": {
            "bool": {
                "must": [
                    {
                        "match": {
                            "imprints.publisher": "Elsevier"
                        }
                    },
                ]
            }
        }
    }
    search_result = es.search(index="scoap3-records-record",  scroll='1m', body=query)
    sid = search_result['_scroll_id']
    scroll_size = len(search_result['hits']['hits'])
    while (scroll_size > 0):
        for record_index in range(scroll_size):
            try:
                files = search_result["hits"]["hits"][record_index]["_source"]["_files"]
            except:
                no_files_at_all[recid] = {'recid': recid, 'doi': doi}
            recid = search_result["hits"]["hits"][record_index]["_source"]["control_number"]
            doi =  search_result["hits"]["hits"][record_index]["_source"]["dois"][0]["value"]
            types = []
            for file in files:
                types.append(file['filetype'])
            if 'pdf/a' not in types:
                no_pdfas[recid] = {'recid': recid, 'doi': doi}
        search_result = es.scroll(scroll_id=sid, scroll='2m')
        sid = search_result['_scroll_id']
        scroll_size = len(search_result['hits']['hits'])
    return {'no_pdfas': no_pdfas, 'no_files_at_all': no_files_at_all}

            




