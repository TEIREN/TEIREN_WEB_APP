import json
import time
import logging
from elasticsearch import Elasticsearch, NotFoundError, ConnectionError

# Elasticsearch 클라이언트를 설정합니다.
es = Elasticsearch(hosts=["http://3.35.81.217:9200"])

# Logging 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 인덱스 매핑 설정
log_index = {
    "linux": "test_linux_syslog",
    "windows": "test_window_syslog",
    "genian": "test_genian_syslog",
    "fortigate": "test_fortigate_syslog"
}

ruleset_mapping = {
    "linux": "linux_ruleset",
    "windows": "window_ruleset",
    "genian": "genian_ruleset",
    "fortigate": "fortigate_ruleset"
}

detected_log_mapping = {
    "linux": "linux_detected_log",
    "windows": "window_detected_log",
    "genian": "genian_detected_log",
    "fortigate": "fortigate_detected_log"
}

# 사용자 선택에 따라 인덱스 설정
def get_index_choice(system):
    if system not in log_index:
        raise ValueError("Invalid system choice.")
    return {
        'log_index_name': log_index[system],
        'ruleset_index': ruleset_mapping[system],
        'detected_log_index': detected_log_mapping[system]
    }

# Bool 쿼리 생성 함수
def construct_bool_query(rule_query):
    bool_query = {
        "bool": {
            "must": [],
            "must_not": []
        }
    }

    for clause in rule_query["query"]["bool"].get("must", []):
        for field, value in clause.get("match", {}).items():
            bool_query["bool"]["must"].append({
                "bool": {
                    "should": [
                        {"match": {field: value}}
                    ],
                    "minimum_should_match": 1
                }
            })
    
    for clause in rule_query["query"]["bool"].get("must_not", []):
        for field, value in clause.get("match", {}).items():
            bool_query["bool"]["must_not"].append({
                "bool": {
                    "should": [
                        {"match": {field: value}}
                    ],
                    "minimum_should_match": 1
                }
            })
    
    return bool_query

# 로그 체크 함수
def check_logs(system):
    index_data = get_index_choice(system)
    log_index_name = index_data['log_index_name']
    ruleset_index = index_data['ruleset_index']
    detected_log_index = index_data['detected_log_index']

    try:
        res = es.search(index=ruleset_index, body={"query": {"match_all": {}}})
        rulesets = res['hits']['hits']

        logger.info(f"Found {len(rulesets)} rulesets in {ruleset_index}")

        for rule in rulesets:
            rule_query = rule["_source"]["query"]
            severity = rule["_source"]["severity"]
            rule_name = rule["_source"]["name"]
            rule_type = rule["_source"].get("rule_type", "custom")  # Default to 'custom' if not present

            logger.info(f"Applying rule: {rule_name}, Query: {json.dumps(rule_query)}")

            bool_query = construct_bool_query(rule_query)

            logger.info(f"Constructed Bool Query: {json.dumps(bool_query, ensure_ascii=False)}")

            log_res = es.search(index=log_index_name, body={"query": bool_query})
            logs_found = log_res['hits']['total']['value']

            logger.info(f"Found {logs_found} logs for rule: {rule_name}")

            if logs_found > 0:
                for log in log_res['hits']['hits']:
                    log_doc = log["_source"]
                    log_doc["detected_by_rule"] = rule_name
                    log_doc["severity"] = severity
                    log_doc["rule_type"] = rule_type  # Add rule_type to the detected log

                    log_id = f"{rule_name}_{log['_id']}"
                    try:
                        es.get(index=detected_log_index, id=log_id)
                        logger.info(f"Log with id {log_id} already exists in {detected_log_index}")
                    except NotFoundError:
                        es.index(index=detected_log_index, id=log_id, body=log_doc)
                        logger.info(f"Indexed log with id {log_id} into {detected_log_index}")
            else:
                logger.info(f"No logs found for rule: {rule_name}")
    except ConnectionError as e:
        logger.error(f"Connection error: {e}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")

# 시스템 선택에 따른 로그 체크 실행
def run_detector(system):
    while True:
        check_logs(system)
        time.sleep(60)  # 60초마다 로그를 체크

if __name__ == "__main__":
    system = "linux"  # 또는 "linux", "windows", "fortigate" 중 하나를 선택
    run_detector(system)
