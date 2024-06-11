"""
대쉬보드 필터링된 결과 원시로그
"""

from elasticsearch import Elasticsearch
import json
from collections import defaultdict, Counter
from datetime import datetime, timedelta, timezone
import time

# Elasticsearch 서버 URL 설정
ELASTICSEARCH_URL = 'http://localhost:9200'
# Elasticsearch 인스턴스 생성
es = Elasticsearch(ELASTICSEARCH_URL)

""""
genian log
"""
def search_genian_logs(start_time=None, end_time=None):
    if start_time and end_time:
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
        }
    else:
        query = {
            "query": {
                "match_all": {}
            },
            "size": 300
        }
    result = es.search(index='test_genian_syslog', body=query)

    session_overtime = defaultdict(int)
    traffic_overtime = defaultdict(lambda: {'sent': 0, 'received': 0})

    for hit in result['hits']['hits']:
        log = hit['_source']
        timestamp = datetime.strptime(log.get('@timestamp'), "%Y-%m-%dT%H:%M:%S.%f")
        time_key = timestamp.strftime('%Y-%m-%d %H:%M')

        session_overtime[time_key] += 1

        sent_byte = int(log.get('sentbyte', 0))
        rcvd_byte = int(log.get('rcvdbyte', 0))
        traffic_overtime[time_key]['sent'] += sent_byte
        traffic_overtime[time_key]['received'] += rcvd_byte

    return session_overtime, traffic_overtime

"""
fortigate log
"""
def search_fortigate_logs(start_time=None, end_time=None):
    if start_time and end_time:
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
        }
    else:
        query = {
            "query": {
                "match_all": {}
            },
            "size": 300
        }
    result = es.search(index='test_fortigate_syslog', body=query)

    src_ip_counter = Counter()
    dst_ip_counter = Counter()
    traffic_by_device = defaultdict(lambda: {'sent': 0, 'received': 0})
    traffic_by_user = defaultdict(lambda: {'sent': 0, 'received': 0})
    traffic_by_application = defaultdict(lambda: {'sent': 0, 'received': 0})
    traffic_by_interface = defaultdict(lambda: {'sent': 0, 'received': 0})

    event_counts = Counter()
    notable_events = Counter()
    latest_events = []

    for hit in result['hits']['hits']:
        log = hit['_source']
        src_ip = log.get('srcip', 'Unknown')
        dst_ip = log.get('dstip', 'Unknown')
        srcintf = log.get('srcintf', 'Unknown')
        dstintf = log.get('dstintf', 'Unknown')
        app = log.get('app', 'Unknown')
        user = log.get('user', 'Unknown')
        sent_byte = int(log.get('sentbyte', 0))
        rcvd_byte = int(log.get('rcvdbyte', 0))

        src_ip_counter[src_ip] += 1
        dst_ip_counter[dst_ip] += 1

        traffic_by_device[src_ip]['sent'] += sent_byte
        traffic_by_device[dst_ip]['received'] += rcvd_byte

        traffic_by_user[user]['sent'] += sent_byte
        traffic_by_user[user]['received'] += rcvd_byte

        traffic_by_application[app]['sent'] += sent_byte
        traffic_by_application[app]['received'] += rcvd_byte

        traffic_by_interface[srcintf]['sent'] += sent_byte
        traffic_by_interface[dstintf]['received'] += rcvd_byte

        # 이벤트 관련 처리
        timestamp = log.get('@timestamp', 'Unknown') # 로그 타임 스템프가 없는 경우 Unknown으로 임시 처리 해두었습니다.
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

    return src_ip_counter, dst_ip_counter, traffic_by_device, traffic_by_user, traffic_by_application, traffic_by_interface, event_counts, notable_events, latest_events

def main():
    initial_run = True
    while True:
        if initial_run:
            print("\n--- Initial Genian Logs ---")
            session_overtime, traffic_overtime = search_genian_logs()
            print(json.dumps({"session_overtime": session_overtime, "traffic_overtime": traffic_overtime}, ensure_ascii=False, indent=4))
            
            print("\n--- Initial Fortigate Logs ---")
            src_ip_counter, dst_ip_counter, traffic_by_device, traffic_by_user, traffic_by_application, traffic_by_interface, event_counts, notable_events, latest_events = search_fortigate_logs()
            print(json.dumps({
                "src_ip_counter": src_ip_counter,
                "dst_ip_counter": dst_ip_counter,
                "traffic_by_device": traffic_by_device,
                "traffic_by_user": traffic_by_user,
                "traffic_by_application": traffic_by_application,
                "traffic_by_interface": traffic_by_interface,
                "event_counts": event_counts,
                "notable_events": notable_events,
                "latest_events": latest_events[:10]
            }, ensure_ascii=False, indent=4))
            
            initial_run = False
        else:
            start_time = (datetime.now(timezone.utc) - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%S.%f")
            end_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")
            
            print("\n--- Genian Logs ---")
            session_overtime, traffic_overtime = search_genian_logs(start_time, end_time)
            print(json.dumps({"session_overtime": session_overtime, "traffic_overtime": traffic_overtime}, ensure_ascii=False, indent=4))
            
            print("\n--- Fortigate Logs ---")
            src_ip_counter, dst_ip_counter, traffic_by_device, traffic_by_user, traffic_by_application, traffic_by_interface, event_counts, notable_events, latest_events = search_fortigate_logs(start_time, end_time)
            print(json.dumps({
                "src_ip_counter": src_ip_counter,
                "dst_ip_counter": dst_ip_counter,
                "traffic_by_device": traffic_by_device,
                "traffic_by_user": traffic_by_user,
                "traffic_by_application": traffic_by_application,
                "traffic_by_interface": traffic_by_interface,
                "event_counts": event_counts,
                "notable_events": notable_events,
                "latest_events": latest_events[:10]
            }, ensure_ascii=False, indent=4))
        
        print("\n--- Waiting for next cycle ---\n")
        time.sleep(30)  # 조정 필요 지속적으로 수집하고 싶으면 삭제하는게 나음

if __name__ == '__main__':
    main()
