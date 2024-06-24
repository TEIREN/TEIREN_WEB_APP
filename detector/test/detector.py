from elasticsearch import Elasticsearch, NotFoundError, ConnectionError

# Elasticsearch 클라이언트를 설정합니다.
es = Elasticsearch(hosts=["http://3.35.81.217:9200"])

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

# 로그 체크 함수
def check_logs(system):
    index_data = get_index_choice(system)
    log_index_name = index_data['log_index_name']
    ruleset_index = index_data['ruleset_index']
    detected_log_index = index_data['detected_log_index']

    try:
        res = es.search(index=ruleset_index, body={"query": {"match_all": {}}})
        rulesets = res['hits']['hits']

        for rule in rulesets:
            rule_query = rule["_source"]["query"]
            severity = rule["_source"]["severity"]
            rule_name = rule["_source"]["name"]

            log_res = es.search(index=log_index_name, body=rule_query)
            logs_found = log_res['hits']['total']['value']

            if logs_found > 0:
                for log in log_res['hits']['hits']:
                    log_doc = log["_source"]
                    log_doc["detected_by_rule"] = rule_name
                    log_doc["severity"] = severity

                    log_id = f"{rule_name}_{log['_id']}"
                    try:
                        es.get(index=detected_log_index, id=log_id)
                    except NotFoundError:
                        es.index(index=detected_log_index, id=log_id, body=log_doc)
    except ConnectionError as e:
        print(f"Connection error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
