"""
ElasticSearch에 새  Index를 만들어 저장을 하는 방법
"""

"""
# Genian Filter Index 조회
curl -X GET "http://localhost:9200/genian_filtered_logs/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match_all": {}
  },
  "size": 10
}
'

# Fortigate Filter Index 조회
curl -X GET "http://localhost:9200/fortigate_filtered_logs/_search?pretty" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match_all": {}
  },
  "size": 10
}
'
"""


from elasticsearch import Elasticsearch, helpers
import json
from collections import defaultdict, Counter
from datetime import datetime, timedelta, timezone
import time

# Elasticsearch 서버 URL 설정
ELASTICSEARCH_URL = 'http://localhost:9200'
# Elasticsearch 인스턴스 생성
es = Elasticsearch(ELASTICSEARCH_URL)

def save_to_elasticsearch(index, data):
    actions = [
        {
            "_index": index,
            "_source": item
        }
        for item in data
    ]
    helpers.bulk(es, actions)

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

    filtered_logs = []

    for hit in result['hits']['hits']:
        log = hit['_source']
        timestamp = datetime.strptime(log.get('@timestamp'), "%Y-%m-%dT%H:%M:%S.%f")
        time_key = timestamp.strftime('%Y-%m-%d %H:%M')

        session_overtime[time_key] += 1

        sent_byte = int(log.get('sentbyte', 0))
        rcvd_byte = int(log.get('rcvdbyte', 0))
        traffic_overtime[time_key]['sent'] += sent_byte
        traffic_overtime[time_key]['received'] += rcvd_byte

        filtered_logs.append({
            "timestamp": timestamp.isoformat(),
            "time_key": time_key,
            "sent_byte": sent_byte,
            "received_byte": rcvd_byte
        })

    save_to_elasticsearch("genian_filtered_logs", filtered_logs)

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

    filtered_logs = []

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

        filtered_logs.append({
            "timestamp": timestamp,
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "srcintf": srcintf,
            "dstintf": dstintf,
            "app": app,
            "user": user,
            "sent_byte": sent_byte,
            "rcvd_byte": rcvd_byte,
            "event_time": event_time.isoformat() if 'event_time' in locals() else 'Unknown',
            "time_key": time_key,
            "action": action
        })

    save_to_elasticsearch("fortigate_filtered_logs", filtered_logs)

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

    return event_counts, notable_events, latest_events

def display_event_results(event_counts, notable_events, latest_events):
    print("\nSystem Events Count:")
    for time_key, count in sorted(event_counts.items()):
        print(f"{time_key}: {count} events")
    
    print("\nNotable Events:")
    for event, count in notable_events.items():
        print(f"{event}: {count} events")
    
    print("\nLatest Events:")
    print(f"{'Time':<20} {'Device':<15} {'Virtual_Domain':<15} {'Subtype':<10} {'Level':<10} {'Action':<10} {'Message':<50}")
    for event in latest_events[:10]:
        print(f"{(event['Time'] or 'Unknown'):<20} {(event['Device'] or 'Unknown'):<15} {(event['Virtual_Domain'] or 'Unknown'):<15} {(event['Subtype'] or 'Unknown'):<10} {(event['Level'] or 'Unknown'):<10} {(event['Action'] or 'Unknown'):<10} {(event['Message'] or 'Unknown'):<50}")

def main():
    initial_run = True
    while True:
        if initial_run:
            print("\n--- Initial Genian Logs ---")
            search_genian_logs()
            
            print("\n--- Initial Fortigate Logs ---")
            event_counts, notable_events, latest_events = search_fortigate_logs()
            display_event_results(event_counts, notable_events, latest_events)
            
            initial_run = False
        else:
            start_time = (datetime.now(timezone.utc) - timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%S.%f")
            end_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")
            
            print("\n--- Genian Logs ---")
            search_genian_logs(start_time, end_time)
            
            print("\n--- Fortigate Logs ---")
            event_counts, notable_events, latest_events = search_fortigate_logs(start_time, end_time)
            display_event_results(event_counts, notable_events, latest_events)
        
        print("\n--- Waiting for next cycle ---\n")
        time.sleep(30)  # 조정 필요 

if __name__ == '__main__':
    main()
