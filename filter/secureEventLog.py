from elasticsearch import Elasticsearch
import json
from collections import defaultdict, Counter
from datetime import datetime, timedelta, timezone
import time


"""
### genian
1. Session Over Time
2. Traffic Over time

### Fortigate
1. Top Source IP
2. Top Destination IP
3. Traffic by Device
4. Traffic by User 
5. Traffic by Application
6. Traffic by Interface
"""

# Elasticsearch 서버 URL 설정
ELASTICSEARCH_URL = 'http://localhost:9200'
# Elasticsearch 인스턴스 생성
es = Elasticsearch(ELASTICSEARCH_URL)

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
            }
        }
    else:
        query = {
            "query": {
                "match_all": {}
            }
        }
    result = es.search(index='test_genian_syslog', body=query, size=300)

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

    print("\nSession Overtime:")
    for time_key, count in sorted(session_overtime.items()):
        print(f"{time_key}: {count} 세션")

    print("\nTraffic Overtime:")
    for time_key, traffic in sorted(traffic_overtime.items()):
        print(f"{time_key} - Sent: {traffic['sent']} bytes, Received: {traffic['received']} bytes")

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
            }
        }
    else:
        query = {
            "query": {
                "match_all": {}
            }
        }
    result = es.search(index='test_fortigate_syslog', body=query, size=300)

    src_ip_counter = Counter()
    dst_ip_counter = Counter()
    traffic_by_device = defaultdict(lambda: {'sent': 0, 'received': 0})
    traffic_by_user = defaultdict(lambda: {'sent': 0, 'received': 0})
    traffic_by_application = defaultdict(lambda: {'sent': 0, 'received': 0})
    traffic_by_interface = defaultdict(lambda: {'sent': 0, 'received': 0})

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

    print("\nTop Source IP:")
    for ip, count in src_ip_counter.most_common(10):
        print(f"{ip}: {count}개")

    print("\nTop Destination IP:")
    for ip, count in dst_ip_counter.most_common(10):
        print(f"{ip}: {count}개")

    print("\nTraffic by Device:")
    for device, traffic in traffic_by_device.items():
        print(f"{device} - Sent: {traffic['sent']} bytes, Received: {traffic['received']} bytes")

    print("\nTraffic by User:")
    for user, traffic in traffic_by_user.items():
        print(f"{user} - Sent: {traffic['sent']} bytes, Received: {traffic['received']} bytes")

    print("\nTraffic by Application:")
    for application, traffic in traffic_by_application.items():
        print(f"{application} - Sent: {traffic['sent']} bytes, Received: {traffic['received']} bytes")

    print("\nTraffic by Interface:")
    for interface, traffic in traffic_by_interface.items():
        print(f"{interface} - Sent: {traffic['sent']} bytes, Received: {traffic['received']} bytes")

def main():
    initial_run = True
    while True:
        if initial_run:
            print("\n--- Initial Genian Logs ---")
            search_genian_logs()
            
            print("\n--- Initial Fortigate Logs ---")
            search_fortigate_logs()
            
            initial_run = False
        else:
            start_time = (datetime.now(timezone.utc) - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%S.%f")
            end_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")
            
            print("\n--- Genian Logs ---")
            search_genian_logs(start_time, end_time)
            
            print("\n--- Fortigate Logs ---")
            search_fortigate_logs(start_time, end_time)
        
        print("\n--- Waiting for next cycle ---\n")
        time.sleep(30)  # 조정 필요 

if __name__ == '__main__':
    main()
