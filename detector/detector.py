import time
from elasticsearch import Elasticsearch, NotFoundError, ConnectionError

# Elasticsearch 클라이언트를 설정합니다.
es = Elasticsearch(hosts=["http://3.35.81.217:9200"])

# 사용할 인덱스 이름들을 정의합니다.
log_index_name = "test_linux_syslog"
ruleset_index = "custom_rulesets"
detected_log_index = "detected_logs"

def check_logs():
    try:
        # 모든 룰셋을 Elasticsearch에서 가져옵니다.
        res = es.search(index=ruleset_index, body={"query": {"match_all": {}}})
        rulesets = res['hits']['hits']

        for rule in rulesets:
            rule_query = rule["_source"]["query"]
            severity = rule["_source"]["severity"]
            rule_name = rule["_source"]["name"]
            
            # 룰셋을 사용하여 로그를 탐지합니다.
            log_res = es.search(index=log_index_name, body=rule_query)
            
            if log_res['hits']['total']['value'] > 0:
                for log in log_res['hits']['hits']:
                    log_doc = log["_source"]
                    log_doc["detected_by_rule"] = rule_name
                    log_doc["severity"] = severity
                    
                    # 탐지된 로그를 저장합니다 (중복 방지)
                    log_id = f"{rule_name}_{log['_id']}"
                    try:
                        # 이미 저장된 로그인지 확인합니다.
                        es.get(index=detected_log_index, id=log_id)
                    except NotFoundError:
                        # 저장되지 않은 로그인 경우에만 저장합니다.
                        es.index(index=detected_log_index, id=log_id, body=log_doc)
                        print(f"Rule '{rule_name}' triggered and log stored with severity {severity}")
                    except Exception as e:
                        print(f"Error checking log existence: {e}")
    except ConnectionError as e:
        print(f"Connection error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

# 주기적으로 로그를 체크합니다.
while True:
    check_logs()
    time.sleep(5)
