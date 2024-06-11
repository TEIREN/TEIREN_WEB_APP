from elasticsearch import Elasticsearch
import json
from datetime import datetime
from collections import defaultdict

# Elasticsearch 서버 URL 설정
ELASTICSEARCH_URL = 'http://localhost:9200'
# Elasticsearch 인스턴스 생성
es = Elasticsearch(ELASTICSEARCH_URL)

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
    result = es.search(index='test_genian_syslog', body=query, params={"size": 100})  
    
    # 위험 수준별 로그 리스트 초기화
    high_risk_logs = []
    medium_risk_logs = []
    low_risk_logs = []

    # 다양한 필터링 조건별 로그 딕셔너리 초기화
    event_type_logs = {}
    log_id_logs = {}
    ip_address_logs = {}
    mac_address_logs = {}

    # Session Overtime 및 Traffic Overtime을 위한 defaultdict 초기화
    session_overtime = defaultdict(int)
    traffic_overtime = defaultdict(lambda: {'sent': 0, 'received': 0})

    # 검색 결과에서 각 로그를 처리
    for hit in result['hits']['hits']:
        log = hit['_source']
        # 로그 정보를 JSON 형식으로 출력 (한글 포함 가능하도록 ensure_ascii=False 설정)
        print(json.dumps(log, indent=4, ensure_ascii=False))

        # @timestamp를 datetime 객체로 변환
        timestamp = datetime.strptime(log.get('@timestamp'), "%Y-%m-%dT%H:%M:%S.%f")
        time_key = timestamp.strftime('%Y-%m-%d %H:%M')  # 시간 단위로 그룹화

        # Session Overtime 집계
        session_overtime[time_key] += 1

        # Traffic Overtime 집계
        # 실제 트래픽 데이터가 없으므로 예시 데이터로 전송 및 수신 바이트 값을 사용
        sent_byte = 0  # 실제 데이터로 대체 필요
        rcvd_byte = 0  # 실제 데이터로 대체 필요
        traffic_overtime[time_key]['sent'] += sent_byte
        traffic_overtime[time_key]['received'] += rcvd_byte

        # 위험 수준별 필터링
        risk_level = log.get('risk_level')
        if risk_level == 'High':
            high_risk_logs.append(log)
        elif risk_level == 'Medium':
            medium_risk_logs.append(log)
        elif risk_level == 'Low':
            low_risk_logs.append(log)

        # 이벤트 유형별 필터링
        event_type = log.get('event_type')
        if event_type:
            if event_type not in event_type_logs:
                event_type_logs[event_type] = []
            event_type_logs[event_type].append(log)

        # 로그 ID별 필터링
        log_id = log.get('log_id')
        if log_id:
            if log_id not in log_id_logs:
                log_id_logs[log_id] = []
            log_id_logs[log_id].append(log)

        # IP 주소별 필터링
        ip_address = log.get('ip_address')
        if ip_address:
            if ip_address not in ip_address_logs:
                ip_address_logs[ip_address] = []
            ip_address_logs[ip_address].append(log)

        # MAC 주소별 필터링
        mac_address = log.get('mac_address')
        if mac_address:
            if mac_address not in mac_address_logs:
                mac_address_logs[mac_address] = []
            mac_address_logs[mac_address].append(log)

    # 위험 수준별 로그 수 출력
    print(f"High: {len(high_risk_logs)}개")
    print(f"Middle: {len(medium_risk_logs)}개")
    print(f"Low: {len(low_risk_logs)}개")

    # 각 필터링 조건별 로그 수 출력
    print("\n이벤트 유형별 로그 수:")
    for key, value in event_type_logs.items():
        print(f"{key}: {len(value)}개")
    
    print("\n로그 ID별 로그 수:")
    for key, value in log_id_logs.items():
        print(f"{key}: {len(value)}개")
    
    print("\nIP 주소별 로그 수:")
    for key, value in ip_address_logs.items():
        print(f"{key}: {len(value)}개")
    
    print("\nMAC 주소별 로그 수:")
    for key, value in mac_address_logs.items():
        print(f"{key}: {len(value)}개")

    # # Session Overtime 출력
    # print("\nSession Overtime:")
    # for time_key, count in sorted(session_overtime.items()):
    #     print(f"{time_key}: {count} 세션")

    # # Traffic Overtime 출력
    # print("\nTraffic Overtime:")
    # for time_key, traffic in sorted(traffic_overtime.items()):
    #     print(f"{time_key} - Sent: {traffic['sent']} bytes, Received: {traffic['received']} bytes")

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
