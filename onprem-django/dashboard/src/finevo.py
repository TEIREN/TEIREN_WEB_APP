from django.shortcuts import render, HttpResponse, redirect

from elasticsearch import Elasticsearch
from collections import defaultdict, Counter
from datetime import datetime, timedelta, timezone
import time
import json
import math

# Elasticsearch 서버 URL 설정
ELASTICSEARCH_URL = 'http://3.35.81.217:9200'
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
        "size": 100000
    } if start_time and end_time else {
        "query": {
            "match_all": {}
        },
        "size": 100000
    }
    es.indices.put_settings(index='test_finevo_genian_syslog', body={"index.max_result_window": 1000000})
    result = es.search(index='test_finevo_genian_syslog', body=query)
    return result['hits']['hits']

# 시간대별 세션 수 계산 함수
def session_overtime_genian(logs):
    session_overtime = defaultdict(int)
    for hit in logs:
        log = hit['_source']
        timestamp = datetime.strptime(log.get('timestamp'), "%Y-%m-%d %H:%M:%S")
        time_key = timestamp.strftime('%Y-%m-%d %H:%M')
        session_overtime[time_key] += 1
    return dict(sorted(session_overtime.items(), key=lambda x: x[0], reverse=False))

# 시간대별 트래픽 계산 함수
def traffic_overtime_genian(logs):
    traffic_overtime = defaultdict(lambda: {'sent': 0, 'received': 0})
    for hit in logs:
        log = hit['_source']
        timestamp = datetime.strptime(log.get('timestamp'), "%Y-%m-%d %H:%M:%S")
        time_key = timestamp.strftime('%Y-%m-%d %H:%M')
        sent_byte = int(log.get('sentbyte', 0))
        rcvd_byte = int(log.get('rcvdbyte', 0))
        traffic_overtime[time_key]['sent'] += sent_byte
        traffic_overtime[time_key]['received'] += rcvd_byte
    return dict(sorted(traffic_overtime.items(), key=lambda x: x[0], reverse=False))

"""
fortigate log
"""

# fortigate 로그를 검색하는 함수
def search_fortigate_logs(start_time=None, end_time=None):
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
        "size": 1000
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
    return dict(sorted(src_ip_counter.items(), key=lambda x: x[1], reverse=True))

# 목적지 IP 상위 10개를 계산하는 함수
def top_destination_ip_fortigate(logs):
    dst_ip_counter = Counter()
    for hit in logs:
        log = hit['_source']
        dst_ip = log.get('dstip', 'Unknown')
        dst_ip_counter[dst_ip] += 1
    return dict(sorted(dst_ip_counter.items(), key=lambda x: x[1], reverse=True))

# 장치별 트래픽 계산 함수
def traffic_by_device_fortigate(logs):
    traffic_by_device = defaultdict(int)
    for hit in logs:
        log = hit['_source']
        device = log.get('vd', 'Unknown')  # vd 필드 사용
        sent_byte = int(log.get('sentbyte', 0))  # sentbyte 필드 사용
        rcvd_byte = int(log.get('rcvdbyte', 0))  # rcvdbyte 필드 사용
        traffic_by_device[device] += sent_byte
        traffic_by_device[device] += rcvd_byte
    return dict(sorted(traffic_by_device.items(), key=lambda x: x[1], reverse=True))

# 사용자별 트래픽 계산 함수
def traffic_by_user_fortigate(logs):
    traffic_by_user = defaultdict(int)
    for hit in logs:
        log = hit['_source']
        user = log.get('user', 'Unknown')
        sent_byte = int(log.get('sentbyte', 0))
        rcvd_byte = int(log.get('rcvdbyte', 0))
        traffic_by_user[user] += sent_byte
        traffic_by_user[user] += rcvd_byte
    return dict(sorted(traffic_by_user.items(), key=lambda x: x[1], reverse=True))

# 애플리케이션별 트래픽 계산 함수
def traffic_by_application_fortigate(logs):
    traffic_by_application = defaultdict(int)
    for hit in logs:
        log = hit['_source']
        app = log.get('app', 'Unknown')
        sent_byte = int(log.get('sentbyte', 0))
        rcvd_byte = int(log.get('rcvdbyte', 0))
        traffic_by_application[app] += sent_byte
        traffic_by_application[app] += rcvd_byte
    return dict(sorted(traffic_by_application.items(), key=lambda x: x[1], reverse=True))

# 인터페이스별 트래픽 계산 함수
def traffic_by_interface_fortigate(logs):
    traffic_by_interface = defaultdict(int)
    for hit in logs:
        log = hit['_source']
        srcintf = log.get('srcintf', 'Unknown')
        dstintf = log.get('dstintf', 'Unknown')
        sent_byte = int(log.get('sentbyte', 0))
        rcvd_byte = int(log.get('rcvdbyte', 0))
        traffic_by_interface[srcintf] += sent_byte
        traffic_by_interface[dstintf] += rcvd_byte
    return dict(sorted(traffic_by_interface.items(), key=lambda x: x[1], reverse=True))

# 이벤트 수 계산 함수
def event_counts_fortigate(logs):
    event_counts = Counter()
    notable_events = Counter()
    latest_events = []
    for hit in logs:
        log = hit['_source']
        # date와 time 필드를 결합하여 timestamp 생성
        timestamp = f"{log.get('date')}T{log.get('time')}"  # date와 time 필드 사용
        if timestamp and timestamp != 'Unknown':
            try:
                event_time = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
                time_key = event_time.strftime('%Y-%m-%d %H:%M')
            except ValueError:
                print(f"Skipping log with invalid timestamp: {timestamp}")
                time_key = 'Unknown'
        else:
            time_key = 'Unknown'

        event_counts[time_key] += 1
        action = log.get('action', 'Unknown')  # action 필드 사용
        notable_events[action] += 1

        latest_events.append({
            "Time": timestamp,
            "Device": log.get('srcintf', 'Unknown'),  # srcintf 필드 사용
            "Virtual_Domain": log.get('vd', 'Unknown'),  # vd 필드 사용
            "Subtype": log.get('subtype', 'Unknown'),  # subtype 필드 사용
            "Level": log.get('level', 'Unknown'),  # level 필드 사용
            "Action": action,
            "Message": log.get('msg', 'Unknown')  # msg 필드 사용
        })

    return dict(sorted(event_counts.items(), key=lambda x: x[0], reverse=True)), dict(sorted(notable_events.items(), key=lambda x: x[1], reverse=True)), latest_events[:10]

def give_colors(_list:list):
    color_list =['#24B6D4','#1cc88a','#f6c23e','#fd7e14','#e74a3b']
    return [color_list[int(i%5)] for i in range(len(_list))]

# 메인 함수
def dashboard(request):
    # print("\n--- Initial Genian Logs ---")/
    genian_logs = search_genian_logs()
    # 시간대별 세션 수 계산
    session_overtime = session_overtime_genian(genian_logs)
    # 시간대별 트래픽 계산
    traffic_overtime = traffic_overtime_genian(genian_logs)
    # print(json.dumps({"session_overtime": session_overtime, "traffic_overtime": traffic_overtime}, ensure_ascii=False, indent=4))
    
    # print("\n--- Initial Fortigate Logs ---")
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
    context = {
        "session_overtime": {'month':list(session_overtime.keys()), 'values': list(session_overtime.values())},
        "traffic_overtime": {'month': list(traffic_overtime.keys()), 'sent': [sent.get('sent', 0) for _,sent in traffic_overtime.items()], 'recieved':[recieved.get('recieved', 0) for _,recieved in traffic_overtime.items()]},
        "src_ip_counter": {'sourceIP': list(src_ip_counter.keys()), 'data': list(src_ip_counter.values()), 'max': int(math.ceil(list(src_ip_counter.values())[0]/100.0)) *100, 'color': give_colors(list(src_ip_counter.keys()))},
        "dst_ip_counter": {'destinationIP': list(dst_ip_counter.keys()), 'data': list(dst_ip_counter.values()), 'max': int(math.ceil(list(dst_ip_counter.values())[0]/100.0)) *100, 'color': give_colors(list(dst_ip_counter.keys()))},
        "traffic_by_device": {'name':list(traffic_by_device.keys()), 'data': list(traffic_by_device.values()), 'color': give_colors(list(traffic_by_device.values()))},
        "traffic_by_user": {'name':list(traffic_by_user.keys()), 'data': list(traffic_by_user.values()), 'color': give_colors(list(traffic_by_user.values()))},
        "traffic_by_application": {'name':list(traffic_by_application.keys()), 'data': list(traffic_by_application.values()), 'color': give_colors(list(traffic_by_application.values()))},
        "traffic_by_interface": {'name':list(traffic_by_interface.keys()), 'data': list(traffic_by_interface.values()), 'color': give_colors(list(traffic_by_interface.values()))},
        "event_counts": {'name': list(event_counts.keys()), 'data': list(event_counts.values()), 'max': int(math.ceil(list(event_counts.values())[0]/100.0)) *100, 'color': give_colors(list(event_counts.keys()))},
        "notable_events": {'name': list(notable_events.keys()), 'data': list(notable_events.values()), 'max': int(math.ceil(list(notable_events.values())[0]/100.0)) *100, 'color': give_colors(list(notable_events.keys()))},
        "latest_events": latest_events
    }
    # print(context)
    return context
