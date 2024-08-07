import json
from elasticsearch import Elasticsearch

ELASTICSEARCH_URL = 'http://localhost:9200'

es = Elasticsearch(ELASTICSEARCH_URL)

def search_all_logs(index_name):
    query = {
        "query": {
            "match_all": {}
        },
        "size": 1000,
        "from": 0
    }

    try:
        es.indices.put_settings(index=index_name, body={"index.max_result_window": 1000000})
        result = es.search(index=index_name, body=query)
        
        # 검색 결과 출력 및 로그 개수 세기
        log_count = 0
        for hit in result['hits']['hits']:
            print(json.dumps(hit['_source'], indent=4, ensure_ascii=False))
            log_count += 1
        print(es.count(index=index_name, query={"match_all": {}})['count'])
        print(f"\nTotal number of logs: {log_count}")
    except Exception as e:
        print(f"Error searching logs: {e}")

def search_all_indices():
    # 모든 인덱스 이름 가져오기
    try:
        # 모든 인덱스 정보를 가져옴
        indices = es.indices.get_alias(index="*")
        # 인덱스 이름 리스트 생성
        index_names = list(indices.keys())
        print("Indices:", index_names)
    except Exception as e:
        print("Error retrieving indices:", e)


def delete_index(index_name):
    try:
        es.indices.delete(index=index_name)
        print(f"Index {index_name} deleted successfully.")
    except Exception as e:
        print(f"Error deleting index {index_name}: {e}")
        
# 함수 실행
if __name__ == "__main__":
    # search_all_logs('userinfo')
    # search_all_logs('linux_syslog')
    search_all_logs('integration_info')
    search_all_logs('mssql_syslog')
    # search_all_logs('window_syslog')
    # search_all_logs('linux_ruleset')
    # search_all_logs('linux_detected_log')
    # search_all_logs('window_detected_log')
    # search_all_logs('fortigate_ruleset')
    # search_all_logs('test_mssql_syslog')
    # search_all_logs('mysql_syslog')
    # search_all_logs('TAG_NAME')
    # search_all_logs('test_finevo_genian_syslog')
    # search_all_logs('test_linux_syslog')
    # search_all_logs('table_property')
    # delete_index('finevo_fortigate_syslog')
    # search_all_indices()
    