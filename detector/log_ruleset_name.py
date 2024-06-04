import time
from elasticsearch import Elasticsearch, ConnectionError

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

# 인덱스 선택
user_choice = get_user_choice()
log_index_name = log_index[user_choice]

# 매핑된 룰셋 인덱스를 설정합니다.
ruleset_index = ruleset_mapping[user_choice]

def check_logs(log_index_name, ruleset_index):
    try:
        # 모든 룰셋을 Elasticsearch에서 가져옵니다.
        res = es.search(index=ruleset_index, body={"query": {"match_all": {}}, "size": 10000})
        rulesets = res['hits']['hits']
        print(f"Total rules found: {len(rulesets)}")

        logs_detected = {}

        for rule in rulesets:
            rule_query = rule["_source"]["query"]["query"]
            rule_name = rule["_source"]["name"]
            severity = rule["_source"]["severity"]

            print(f"Checking rule: {rule_name} with severity {severity}")

            # 룰셋을 사용하여 로그를 탐지합니다.
            log_res = es.search(index=log_index_name, body={"query": rule_query, "size": 10000})
            logs_found = log_res['hits']['total']['value']
            print(f"Logs found for rule {rule_name}: {logs_found}")

            if logs_found > 0:
                for log in log_res['hits']['hits']:
                    log_id = log["_id"]
                    log_doc = log["_source"]

                    if log_id not in logs_detected:
                        logs_detected[log_id] = log_doc
                        logs_detected[log_id]["detected_by_rules"] = []
                        logs_detected[log_id]["severity"] = severity

                    logs_detected[log_id]["detected_by_rules"].append(rule_name)

        for log_id, log_doc in logs_detected.items():
            print(log_doc)

    except ConnectionError as e:
        print(f"Connection error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

# 주기적으로 로그를 체크합니다.
while True:
    check_logs(log_index_name, ruleset_index)
    time.sleep(2)
