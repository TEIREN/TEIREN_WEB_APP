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
        result = es.search(index=index_name, body=query, size=10)
        
        # 검색 결과 출력 및 로그 개수 세기
        log_count = 0
        for hit in result['hits']['hits']:
            print(json.dumps(hit['_source'], indent=4, ensure_ascii=False))
            log_count += 1
        
        print(f"\nTotal number of logs: {log_count}")
    except Exception as e:
        print(f"Error searching logs: {e}")

# 함수 실행
if __name__ == "__main__":
    # search_all_logs('userinfo')
    search_all_logs('test_finevo_fortigate_syslog')
    search_all_logs('test_finevo_genian')
    # search_all_logs('test_window_syslog')
    # search_all_logs('linux_ruleset')
    # search_all_logs('linux_detected_log')
    # search_all_logs('window_detected_log')
    # search_all_logs('fortigate_ruleset')
    # search_all_logs('test_mssql_syslog')
    # search_all_logs('test_fortigate_syslog')