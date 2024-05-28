import time
from elasticsearch import Elasticsearch, NotFoundError, ConnectionError

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

# detected log 인덱스 이름 매핑
detected_log_mapping = {
    1: "linux_detected_log",
    2: "window_detected_log",
    3: "genian_detected_log",
    4: "fortigate_detected_log"
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

# 매핑된 룰셋 인덱스와 디텍티드 로그 인덱스를 설정합니다.
ruleset_index = ruleset_mapping[user_choice]
detected_log_index = detected_log_mapping[user_choice]

def check_logs_linux():
    try:
        # 모든 룰셋을 Elasticsearch에서 가져옵니다.
        res = es.search(index=ruleset_index, body={"query": {"match_all": {}}, "size": 10000})
        rulesets = res['hits']['hits']
        print(f"Total rules found: {len(rulesets)}")

        for rule in rulesets:
            rule_query = rule["_source"]["query"]
            severity = rule["_source"]["severity"]
            rule_name = rule["_source"]["name"]
            
            print(f"Checking rule: {rule_name} with severity {severity}")
            
            # 룰셋을 사용하여 로그를 탐지합니다.
            log_res = es.search(index=log_index_name, body={**rule_query, "size": 10000})
            logs_found = log_res['hits']['total']['value']
            print(f"Logs found for rule {rule_name}: {logs_found}")
                    
            if logs_found > 0:
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

def check_logs_windows():
    try:
        # 모든 룰셋을 Elasticsearch에서 가져옵니다.
        res = es.search(index=ruleset_index, body={"query": {"match_all": {}}, "size": 10000})
        rulesets = res['hits']['hits']
        print(f"Total rules found: {len(rulesets)}")

        for rule in rulesets:
            rule_query = rule["_source"]["query"]["query"]
            severity = rule["_source"]["severity"]
            rule_name = rule["_source"]["name"]
            
            print(f"Checking rule: {rule_name} with severity {severity}")
            
            # 룰셋을 사용하여 로그를 탐지합니다.
            log_res = es.search(index=log_index_name, body={"query": rule_query, "size": 10000})
            logs_found = log_res['hits']['total']['value']
            print(f"Logs found for rule {rule_name}: {logs_found}")
                    
            if logs_found > 0:
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
    if user_choice == 1:
        check_logs_linux()
    elif user_choice == 2:
        check_logs_windows()
    time.sleep(2)
