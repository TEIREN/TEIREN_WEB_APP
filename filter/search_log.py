import json
from elasticsearch import Elasticsearch

ELASTICSEARCH_URL = 'http://localhost:9200'

es = Elasticsearch(ELASTICSEARCH_URL)

def search_all_logs(index_name):
    query = {
        "query": {
            "match_all": {}
        }
    }
    
    try:
        result = es.search(index=index_name, body=query, size=10000)  
        
        # 검색 결과 출력
        for hit in result['hits']['hits']:
            print(json.dumps(hit['_source'], indent=4, ensure_ascii=False))
    except Exception as e:
        print(f"Error searching logs: {e}")

# 함수 실행
if __name__ == "__main__":
    # search_all_logs('test_fortigate_syslog')
    search_all_logs('fortigate_ruleset')
    # search_all_logs('linux_detected_log')