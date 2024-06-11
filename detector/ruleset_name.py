import time
from elasticsearch import Elasticsearch, NotFoundError, ConnectionError
import json

# Elasticsearch 클라이언트를 설정합니다.
es = Elasticsearch(hosts=["http://3.35.81.217:9200"])

# 탐지 대상 로그 인덱스
log_index = {
    1: "test_linux_syslog",
    2: "test_window_syslog",
    3: "test_genian_syslog",
    4: "test_fortigate_syslog"
}

# 룰셋 인덱스 이름 매핑
ruleset_mapping = {
    1: "linux_ruleset",
    2: "window_ruleset",
    3: "genian_ruleset",
    4: "fortigate_ruleset"
}

# 사용자로부터 인덱스 선택을 입력받습니다.
def get_user_choice():
    print("Select the index to use:")
    print("1. Linux")
    print("2. Windows")
    print("3. Genian")
    print("4. Fortigate")
    choice = int(input("Enter your choice (1-4): "))
    if choice not in [1, 2, 3, 4]:
        raise ValueError("Invalid choice, please select a number between 1 and 4.")
    return choice

# 특정 룰셋을 조회하고 탐지된 로그를 출력하는 함수
def get_ruleset_and_detect_logs(index_name, ruleset_index):
    ruleset_name = input("Enter the name of the ruleset: ")
    try:
        # 룰셋을 Elasticsearch에서 가져옵니다.
        res = es.search(index=ruleset_index, body={"query": {"match": {"name": ruleset_name}}})
        if res['hits']['total']['value'] == 0:
            print(f"No ruleset found with the name: {ruleset_name}")
            return
        rule = res['hits']['hits'][0]['_source']
        print("Ruleset JSON:")
        print(json.dumps(rule, indent=4))

        rule_query = rule["query"]["query"]
        rule_name = rule["name"]
        severity = rule["severity"]

        print(f"\nChecking rule: {rule_name} with severity {severity}")

        # 룰셋을 사용하여 로그를 탐지합니다.
        log_res = es.search(index=index_name, body={"query": rule_query, "size": 10000})
        logs_found = log_res['hits']['total']['value']
        print(f"Logs found for rule {rule_name}: {logs_found}")

        if logs_found > 0:
            for log in log_res['hits']['hits']:
                log_doc = log["_source"]
                log_doc["detected_by_rule"] = rule_name
                log_doc["severity"] = severity
                print(json.dumps(log_doc, indent=4))

    except ConnectionError as e:
        print(f"Connection error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

# 인덱스 선택
user_choice = get_user_choice()
log_index_name = log_index[user_choice]
ruleset_index = ruleset_mapping[user_choice]

# 특정 룰셋을 조회하고 탐지된 로그를 출력합니다.
get_ruleset_and_detect_logs(log_index_name, ruleset_index)
