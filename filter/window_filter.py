"""
----
High Risk (높은 위험도)
4625: 계정 로그인 실패
4672: 특수 권한 할당
4688: 새로운 프로세스 생성
4647: 계정 로그오프
4697: 새로운 서비스 설치
----
Medium Risk (중간 위험도)
4624: 계정 로그인 성공
4648: 명시적 자격 증명을 사용하는 로그인 시도
4663: 개체 액세스 시도
4670: 권한 있는 개체 수정
Low Risk (낮은 위험도)
4634: 계정 로그오프
4907: 감사 정책 변경
4912: 변경된 보안 감사 설정
----
"""

from elasticsearch import Elasticsearch
import json
from datetime import datetime

# Elasticsearch 서버 URL 설정
ELASTICSEARCH_URL = 'http://localhost:9200'
# Elasticsearch 인스턴스 생성
es = Elasticsearch(ELASTICSEARCH_URL)

def evaluate_risk(log):
    """로그의 위험도를 평가하는 함수"""
    # 위험도를 평가하기 위한 기본 점수
    high_risk_event_ids = {4625, 4672, 4688, 4647, 4697}  # 높은 위험도의 이벤트 ID
    medium_risk_event_ids = {4624, 4648, 4663, 4670}  # 중간 위험도의 이벤트 ID

    event_id = log.get('EventID')
    if event_id in high_risk_event_ids:
        return 'High'
    elif event_id in medium_risk_event_ids:
        return 'Middle'
    else:
        return 'Low'

def search_logs(start_time=None, end_time=None):
    if start_time and end_time:
        # 시간 범위가 주어진 경우의 쿼리 생성
        query = {
            "query": {
                "range": {
                    "@timestamp": {
                        "gte": start_time,
                        "lte": end_time,
                        "format": "yyyy-MM-dd'T'HH:mm:ss.SSSSSS" # 시간 형식 지정
                    }
                }
            }
        }
    else:
        # 시간 범위가 주어지지 않은 경우의 쿼리 생성
        query = {
            "query": {
                "match_all": {}
            }
        }
    
    # Elasticsearch에서 쿼리 실행
    result = es.search(index='test_window_syslog', body=query, size=10000)  
    
    # 필터링 조건별 로그 리스트 초기화
    event_id_logs = {}
    channel_logs = {}
    source_name_logs = {}
    event_type_logs = {}
    ip_address_logs = {}
    risk_logs = {
        'High': [],
        'Middle': [],
        'Low': []
    }

    # 검색 결과에서 각 로그를 처리
    for hit in result['hits']['hits']:
        log = hit['_source']

        # 로그의 위험도 평가
        risk_level = evaluate_risk(log)
        risk_logs[risk_level].append(log)

        # JSON 형식으로 로그 출력
        print(json.dumps(log, indent=4, ensure_ascii=False))

        # 이벤트 ID 별 필터링
        event_id = log.get('EventID')
        if event_id:
            if event_id not in event_id_logs:
                event_id_logs[event_id] = []
            event_id_logs[event_id].append(log)

        # 채널별 필터링
        channel = log.get('Channel')
        if channel:
            if channel not in channel_logs:
                channel_logs[channel] = []
            channel_logs[channel].append(log)

        # 출처 이름별 필터링
        source_name = log.get('SourceName')
        if source_name:
            if source_name not in source_name_logs:
                source_name_logs[source_name] = []
            source_name_logs[source_name].append(log)

        # 이벤트 유형별 필터링
        event_type = log.get('EventType')
        if event_type:
            if event_type not in event_type_logs:
                event_type_logs[event_type] = []
            event_type_logs[event_type].append(log)

        # IP 주소에 따른 필터링
        ip_address = log.get('teiren_request_ip')
        if ip_address:
            if ip_address not in ip_address_logs:
                ip_address_logs[ip_address] = []
            ip_address_logs[ip_address].append(log)

    # 각 필터링 조건별 로그 수 출력
    print("\n이벤트 ID별 로그 수:")
    for key, value in event_id_logs.items():
        print(f"{key}: {len(value)}개")
    
    print("\n채널별 로그 수:")
    for key, value in channel_logs.items():
        print(f"{key}: {len(value)}개")
    
    print("\n출처 이름별 로그 수:")
    for key, value in source_name_logs.items():
        print(f"{key}: {len(value)}개")

    print("\n이벤트 유형별 로그 수:")
    for key, value in event_type_logs.items():
        print(f"{key}: {len(value)}개")

    print("\n위험도별 로그 수:")
    for key, value in risk_logs.items():
        print(f"{key}: {len(value)}개")

    print("\nIP 주소별 로그 수:")
    for key, value in ip_address_logs.items():
        print(f"{key}: {len(value)}개")

def main():
    choice = input("전체 시간을 검색하시겠습니까? (y/n): ").strip().lower()
    if choice == 'y':
        search_logs()
    else:
        start_time = input("시작 시간을 입력하세요 (예: YYYY-MM-DDT00:00:00.000000): ")
        end_time = input("종료 시간을 입력하세요 (예: YYYY-MM-DDT23:59:59.999999): ")
        search_logs(start_time, end_time)

if __name__ == '__main__':
    main()
