from elasticsearch import Elasticsearch

es = Elasticsearch(["http://localhost:9200"])

def fetch_log_properties(index, exclude_keys):
    query = {
        "query": {
            "match_all": {}
        },
        "size": 1000
    }
    
    response = es.search(index=index, body=query)
    
    hits = response['hits']['hits']
    
    properties = {}
    for hit in hits:
        log = hit['_source']
        for key, value in log.items():
            if key not in exclude_keys:
                if key not in properties:
                    properties[key] = set()
                if isinstance(value, (str, int, float, bool)): 
                    properties[key].add(value)
    
    properties_list = [{key: list(values)} for key, values in properties.items()]
    
    return properties_list

index = "test_fortigate_syslog"
exclude_keys = {'date', 'time', 'eventtime'} # 제외할 로그 프라퍼티

log_properties = fetch_log_properties(index, exclude_keys)

for prop_dict in log_properties:
    print(prop_dict)
