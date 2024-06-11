from elasticsearch import Elasticsearch
import json
from collections import defaultdict, Counter
from datetime import datetime, timedelta, timezone
import time

# Elasticsearch 서버 URL 설정
ELASTICSEARCH_URL = 'http://localhost:9200'
# Elasticsearch 인스턴스 생성
es = Elasticsearch(ELASTICSEARCH_URL)

"""
genian log
"""

# genian 로그를 검색하는 함수
def search_genian_logs(start_time=None, end_time=None):
    # 시간 범위가 주어졌을 때와 아닐 때의 쿼리 생성
    query = {
        "query": {
            "range": {
                "@timestamp": {
                    "gte": start_time,
                    "lte": end_time,
                    "format": "yyyy-MM-dd'T'HH:mm:ss.SSSSSS"
                }
            }
        },
        "size": 300
    } if start_time and end_time else {
        "query": {
            "match_all": {}
        },
        "size": 300
    }
    result = es.search(index='test_genian_syslog', body=query)
    return result['hits']['hits']

# 시간대별 세션 수 계산 함수
def session_overtime_genian(logs):
    session_overtime = defaultdict(int)
    for hit in logs:
        log = hit['_source']
        timestamp = datetime.strptime(log.get('@timestamp'), "%Y-%m-%dT%H:%M:%S.%f")
        time_key = timestamp.strftime('%Y-%m-%d %H:%M')
        session_overtime[time_key] += 1
    return session_overtime

# 시간대별 트래픽 계산 함수
def traffic_overtime_genian(logs):
    traffic_overtime = defaultdict(lambda: {'sent': 0, 'received': 0})
    for hit in logs:
        log = hit['_source']
        timestamp = datetime.strptime(log.get('@timestamp'), "%Y-%m-%dT%H:%M:%S.%f")
        time_key = timestamp.strftime('%Y-%m-%d %H:%M')
        sent_byte = int(log.get('sentbyte', 0))
        rcvd_byte = int(log.get('rcvdbyte', 0))
        traffic_overtime[time_key]['sent'] += sent_byte
        traffic_overtime[time_key]['received'] += rcvd_byte
    return traffic_overtime

"""
fortigate log
"""

# fortigate 로그를 검색하는 함수
def search_fortigate_logs(start_time=None, end_time=None):
    # 시간 범위가 주어졌을 때와 아닐 때의 쿼리 생성
    query = {
        "query": {
            "range": {
                "@timestamp": {
                    "gte": start_time,
                    "lte": end_time,
                    "format": "yyyy-MM-dd'T'HH:mm:ss.SSSSSS"
                }
            }
        },
        "size": 300
    } if start_time and end_time else {
        "query": {
            "match_all": {}
        },
        "size": 300
    }
    result = es.search(index='test_fortigate_syslog', body=query)
    return result['hits']['hits']

# 소스 IP 상위 10개를 계산하는 함수
def top_source_ip_fortigate(logs):
    src_ip_counter = Counter()
    for hit in logs:
        log = hit['_source']
        src_ip = log.get('srcip', 'Unknown')
        src_ip_counter[src_ip] += 1
    return src_ip_counter

# 목적지 IP 상위 10개를 계산하는 함수
def top_destination_ip_fortigate(logs):
    dst_ip_counter = Counter()
    for hit in logs:
        log = hit['_source']
        dst_ip = log.get('dstip', 'Unknown')
        dst_ip_counter[dst_ip] += 1
    return dst_ip_counter

# 장치별 트래픽 계산 함수
def traffic_by_device_fortigate(logs):
    traffic_by_device = defaultdict(lambda: {'sent': 0, 'received': 0})
    for hit in logs:
        log = hit['_source']
        src_ip = log.get('srcip', 'Unknown')
        dst_ip = log.get('dstip', 'Unknown')
        sent_byte = int(log.get('sentbyte', 0))
        rcvd_byte = int(log.get('rcvdbyte', 0))
        traffic_by_device[src_ip]['sent'] += sent_byte
        traffic_by_device[dst_ip]['received'] += rcvd_byte
    return traffic_by_device

# 사용자별 트래픽 계산 함수
def traffic_by_user_fortigate(logs):
    traffic_by_user = defaultdict(lambda: {'sent': 0, 'received': 0})
    for hit in logs:
        log = hit['_source']
        user = log.get('user', 'Unknown')
        sent_byte = int(log.get('sentbyte', 0))
        rcvd_byte = int(log.get('rcvdbyte', 0))
        traffic_by_user[user]['sent'] += sent_byte
        traffic_by_user[user]['received'] += rcvd_byte
    return traffic_by_user

# 애플리케이션별 트래픽 계산 함수
def traffic_by_application_fortigate(logs):
    traffic_by_application = defaultdict(lambda: {'sent': 0, 'received': 0})
    for hit in logs:
        log = hit['_source']
        app = log.get('app', 'Unknown')
        sent_byte = int(log.get('sentbyte', 0))
        rcvd_byte = int(log.get('rcvdbyte', 0))
        traffic_by_application[app]['sent'] += sent_byte
        traffic_by_application[app]['received'] += rcvd_byte
    return traffic_by_application

# 인터페이스별 트래픽 계산 함수
def traffic_by_interface_fortigate(logs):
    traffic_by_interface = defaultdict(lambda: {'sent': 0, 'received': 0})
    for hit in logs:
        log = hit['_source']
        srcintf = log.get('srcintf', 'Unknown')
        dstintf = log.get('dstintf', 'Unknown')
        sent_byte = int(log.get('sentbyte', 0))
        rcvd_byte = int(log.get('rcvdbyte', 0))
        traffic_by_interface[srcintf]['sent'] += sent_byte
        traffic_by_interface[dstintf]['received'] += rcvd_byte
    return traffic_by_interface

# 이벤트 수 계산 함수
def event_counts_fortigate(logs):
    event_counts = Counter()
    notable_events = Counter()
    latest_events = []
    for hit in logs:
        log = hit['_source']
        timestamp = log.get('@timestamp', 'Unknown')
        if timestamp and timestamp != 'Unknown':
            try:
                event_time = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f")
                time_key = event_time.strftime('%Y-%m-%d %H:%M')
            except ValueError:
                print(f"Skipping log with invalid timestamp: {timestamp}")
                time_key = 'Unknown'
        else:
            time_key = 'Unknown'
        
        event_counts[time_key] += 1
        action = log.get('action', 'Unknown')
        notable_events[action] += 1

        latest_events.append({
            "Time": timestamp,
            "Device": log.get('device', 'Unknown'),
            "Virtual_Domain": log.get('vd', 'Unknown'),
            "Subtype": log.get('subtype', 'Unknown'),
            "Level": log.get('level', 'Unknown'),
            "Action": action,
            "Message": log.get('msg', 'Unknown')
        })

    return event_counts, notable_events, latest_events[:10]

# 메인 함수
def main():
    initial_run = True
    while True:
        if initial_run:
            print("\n--- Initial Genian Logs ---")
            genian_logs = search_genian_logs()
            # 시간대별 세션 수 계산
            session_overtime = session_overtime_genian(genian_logs)
            # 시간대별 트래픽 계산
            traffic_overtime = traffic_overtime_genian(genian_logs)
            print(json.dumps({"session_overtime": session_overtime, "traffic_overtime": traffic_overtime}, ensure_ascii=False, indent=4))
            
            print("\n--- Initial Fortigate Logs ---")
            fortigate_logs = search_fortigate_logs()
            # 상위 소스 IP 계산
            src_ip_counter = top_source_ip_fortigate(fortigate_logs)
            # 상위 목적지 IP 계산
            dst_ip_counter = top_destination_ip_fortigate(fortigate_logs)
            # 장치별 트래픽 계산
            traffic_by_device = traffic_by_device_fortigate(fortigate_logs)
            # 사용자별 트래픽 계산
            traffic_by_user = traffic_by_user_fortigate(fortigate_logs)
            # 애플리케이션별 트래픽 계산
            traffic_by_application = traffic_by_application_fortigate(fortigate_logs)
            # 인터페이스별 트래픽 계산
            traffic_by_interface = traffic_by_interface_fortigate(fortigate_logs)
            # 이벤트 수 계산 및 최신 이벤트 가져오기
            event_counts, notable_events, latest_events = event_counts_fortigate(fortigate_logs)
            print(json.dumps({
                "src_ip_counter": src_ip_counter,
                "dst_ip_counter": dst_ip_counter,
                "traffic_by_device": traffic_by_device,
                "traffic_by_user": traffic_by_user,
                "traffic_by_application": traffic_by_application,
                "traffic_by_interface": traffic_by_interface,
                "event_counts": event_counts,
                "notable_events": notable_events,
                "latest_events": latest_events
            }, ensure_ascii=False, indent=4))
            
            initial_run = False
        else:
            # 최근 5분간의 로그를 검색
            start_time = (datetime.now(timezone.utc) - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%S.%f")
            end_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")
            
            print("\n--- Genian Logs ---")
            genian_logs = search_genian_logs(start_time, end_time)
            session_overtime = session_overtime_genian(genian_logs)
            traffic_overtime = traffic_overtime_genian(genian_logs)
            print(json.dumps({"session_overtime": session_overtime, "traffic_overtime": traffic_overtime}, ensure_ascii=False, indent=4))
            
            print("\n--- Fortigate Logs ---")
            fortigate_logs = search_fortigate_logs(start_time, end_time)
            src_ip_counter = top_source_ip_fortigate(fortigate_logs)
            dst_ip_counter = top_destination_ip_fortigate(fortigate_logs)
            traffic_by_device = traffic_by_device_fortigate(fortigate_logs)
            traffic_by_user = traffic_by_user_fortigate(fortigate_logs)
            traffic_by_application = traffic_by_application_fortigate(fortigate_logs)
            traffic_by_interface = traffic_by_interface_fortigate(fortigate_logs)
            event_counts, notable_events, latest_events = event_counts_fortigate(fortigate_logs)
            print(json.dumps({
                "src_ip_counter": src_ip_counter,
                "dst_ip_counter": dst_ip_counter,
                "traffic_by_device": traffic_by_device,
                "traffic_by_user": traffic_by_user,
                "traffic_by_application": traffic_by_application,
                "traffic_by_interface": traffic_by_interface,
                "event_counts": event_counts,
                "notable_events": notable_events,
                "latest_events": latest_events
            }, ensure_ascii=False, indent=4))
        
        print("\n--- Waiting for next cycle ---\n")
        # 30초 대기 (필요에 따라 조정 가능) 계속 가져올거면 예외 처리
        time.sleep(30)

if __name__ == '__main__':
    main()
