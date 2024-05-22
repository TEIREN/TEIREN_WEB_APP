from elasticsearch import Elasticsearch
from datetime import datetime

# Elasticsearch 클라이언트 초기화
es = Elasticsearch(hosts=["http://3.35.81.217:9200"])

# 특정 인덱스에서 로그를 가져오는 함수
def get_logs(index_name, query=None):
    body = {
        "query": {
            "match_all": {}  # 모든 로그를 가져옴
        }
    }
    if query:
        body["query"] = query

    res = es.search(index=index_name, body=body)
    return res["hits"]["hits"]

# 규칙 적용하여 이벤트를 탐지하는 함수
def detect_events(logs, rules):
    detected_events = []
    for log in logs:
        for rule in rules:
            if rule_matches(log, rule):
                detected_events.append({
                    "timestamp": log["_source"]["@timestamp"],
                    "event": rule["name"],
                    "severity": rule["severity"]
                })
                break  # 하나의 로그가 여러 규칙에 매치될 수 있으므로, 매치되면 다음 규칙으로 넘어감
    return detected_events

# 로그와 규칙을 비교하여 매치 여부를 확인하는 함수
def rule_matches(log, rule):
    # 여기에 로그와 규칙을 비교하는 코드를 추가
    # 예를 들어, 로그의 메시지와 프로그램 이름을 규칙과 비교하여 매치되면 True를 반환하도록 함
    return True

if __name__ == "__main__":
    # 규칙셋 설정
    rules = [
        {
            "name": "Detect systemd failure",
            "system": "linux",
            "query": {
                "message": "fail", # 메세지 수정해야할듯 
                "programname": "systemd"
            },
            "severity": 4
        }
        # 추가 규칙들도 필요에 따라 설정
    ]

    # 로그 가져오기
    logs = get_logs("test_linux_syslog")

    # 이벤트 탐지
    detected_events = detect_events(logs, rules)

    # 탐지된 이벤트 출력 또는 로그
    for event in detected_events:
        print(event)
