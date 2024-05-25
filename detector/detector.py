import time
from elasticsearch import Elasticsearch, NotFoundError, ConnectionError

es = Elasticsearch(hosts=["http://3.35.81.217:9200"])
log_index_name = "test_linux_syslog"
ruleset_index = "custom_rulesets"
detected_log_index = "detected_logs"

def check_logs():
    try:
        # 룰셋을 가져옵니다
        res = es.search(index=ruleset_index, body={"query": {"match_all": {}}})
        rulesets = res['hits']['hits']

        for rule in rulesets:
            rule_query = rule["_source"]["query"]
            severity = rule["_source"]["severity"]
            rule_name = rule["_source"]["name"]
            
            # 로그를 룰셋 기준으로 탐지합니다
            log_res = es.search(index=log_index_name, body=rule_query)
            
            if log_res['hits']['total']['value'] > 0:
                for log in log_res['hits']['hits']:
                    log_doc = log["_source"]
                    log_doc["detected_by_rule"] = rule_name
                    log_doc["severity"] = severity
                    
                    # 탐지된 로그를 저장합니다 (중복 방지)
                    log_id = log["_id"]
                    try:
                        es.get(index=detected_log_index, id=log_id)
                    except NotFoundError:
                        es.index(index=detected_log_index, id=log_id, body=log_doc)
                        print(f"Rule '{rule_name}' triggered and log stored with severity {severity}")
                    except Exception as e:
                        print(f"Error checking log existence: {e}")
    except ConnectionError as e:
        print(f"Connection error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

while True:
    check_logs()
    time.sleep(5)
