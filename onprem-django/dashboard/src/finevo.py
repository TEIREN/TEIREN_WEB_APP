from elasticsearch import Elasticsearch
from collections import defaultdict, Counter
from datetime import datetime
import math

# Elasticsearch 서버 URL 설정
ELASTICSEARCH_URL = "http://3.35.81.217:9200"
# Elasticsearch 인스턴스 생성
es = Elasticsearch(ELASTICSEARCH_URL)

class FortigateDashboard:
    def __init__(self, start_time=None, end_time=None):
        query = (
            {
                "query": {
                    "range": {
                        "@timestamp": {
                            "gte": start_time,
                            "lte": end_time,
                            "format": "yyyy-MM-dd'T'HH:mm:ss.SSSSSS",
                        }
                    }
                },
                "size": 100000,
            }
            if start_time and end_time
            else {"query": {"match_all": {}}, "size": 100000}
        )
        es.indices.put_settings(
            index="test_finevo_genian_syslog", body={"index.max_result_window": 1000000}
        )
        result = es.search(index="finevo_fortigate_syslog", body=query)
        self.log_list = result["hits"]["hits"]

    def get_dashboard_data(self):
        # 시간대별 세션 수 계산
        session_overtime = self.session_overtime_fortigate()
        # 시간대별 트래픽 계산
        traffic_overtime = self.traffic_overtime_fortigate()
        # 상위 소스 IP 계산
        src_ip_counter = self.top_source_ip_fortigate()
        # 상위 목적지 IP 계산
        dst_ip_counter = self.top_destination_ip_fortigate()
        # 장치별 트래픽 계산
        traffic_by_device = self.traffic_by_device_fortigate()
        # 사용자별 트래픽 계산
        traffic_by_user = self.traffic_by_user_fortigate()
        # 애플리케이션별 트래픽 계산
        traffic_by_application = self.traffic_by_application_fortigate()
        # 인터페이스별 트래픽 계산
        traffic_by_interface = self.traffic_by_interface_fortigate()
        # 이벤트 수 계산 및 최신 이벤트 가져오기
        event_counts, notable_events, latest_events = self.event_counts_fortigate()
        response = {
            "session_overtime": {
                "month": list(session_overtime.keys()),
                "values": list(session_overtime.values()),
            },
            "traffic_overtime": {
                "month": list(traffic_overtime.keys()),
                "sent": [sent.get("sent", 0) for _, sent in traffic_overtime.items()],
                "received": [
                    received.get("received", 0)
                    for _, received in traffic_overtime.items()
                ],
            },
            "src_ip_counter": {
                "sourceIP": list(src_ip_counter.keys()),
                "data": list(src_ip_counter.values()),
                "max": int(math.ceil(list(src_ip_counter.values())[0] / 100.0)) * 100,
                "color": self.give_colors(list(src_ip_counter.keys())),
            },
            "dst_ip_counter": {
                "destinationIP": list(dst_ip_counter.keys()),
                "data": list(dst_ip_counter.values()),
                "max": int(math.ceil(list(dst_ip_counter.values())[0] / 100.0)) * 100,
                "color": self.give_colors(list(dst_ip_counter.keys())),
            },
            "traffic_by_device": {
                "name": list(traffic_by_device.keys()),
                "data": list(traffic_by_device.values()),
                "color": self.give_colors(list(traffic_by_device.values())),
            },
            "traffic_by_user": {
                "name": list(traffic_by_user.keys()),
                "data": list(traffic_by_user.values()),
                "color": self.give_colors(list(traffic_by_user.values())),
            },
            "traffic_by_application": {
                "name": list(traffic_by_application.keys()),
                "data": list(traffic_by_application.values()),
                "color": self.give_colors(list(traffic_by_application.values())),
            },
            "traffic_by_interface": {
                "name": list(traffic_by_interface.keys()),
                "data": list(traffic_by_interface.values()),
                "color": self.give_colors(list(traffic_by_interface.values())),
            },
            "event_counts": {
                "name": list(event_counts.keys()),
                "data": list(event_counts.values()),
                "max": int(math.ceil(max(event_counts.values()) / 100.0)) * 100,
                "color": self.give_colors(list(event_counts.keys())),
            },
            "notable_events": {
                "name": list(notable_events.keys()),
                "data": list(notable_events.values()),
                "max": int(math.ceil(list(notable_events.values())[0] / 100.0)) * 100,
                "color": self.give_colors(list(notable_events.keys())),
            },
            "latest_events": latest_events,
        }
        return response

    # 시간대별 세션 수 계산 함수
    def session_overtime_fortigate(self):
        session_overtime = defaultdict(int)
        for hit in self.log_list:
            log = hit["_source"]
            timestamp = datetime.fromtimestamp(
                int(log.get("eventtime")) / 1_000_000_000
            )
            time_key = timestamp.strftime("%Y-%m-%d %H:%M")
            session_overtime[time_key] += 1
        return dict(sorted(session_overtime.items(), key=lambda x: x[0], reverse=False))

    # 시간대별 트래픽 계산 함수
    def traffic_overtime_fortigate(self):
        traffic_overtime = defaultdict(lambda: {"sent": 0, "received": 0})
        for hit in self.log_list:
            log = hit["_source"]
            timestamp = datetime.fromtimestamp(
                int(log.get("eventtime")) / 1_000_000_000
            )
            time_key = timestamp.strftime("%Y-%m-%d %H:%M")
            sent_byte = float(log.get("sentbyte", 0))
            rcvd_byte = float(log.get("rcvdbyte", 0))
            if sent_byte + rcvd_byte == 0:
                continue
            traffic_overtime[time_key]["sent"] += (
                round(sent_byte / 1000) if sent_byte > 0 else 0
            )
            traffic_overtime[time_key]["received"] += (
                round(rcvd_byte / 1000) if rcvd_byte > 0 else 0
            )
        return dict(sorted(traffic_overtime.items(), key=lambda x: x[0], reverse=False))

    # 소스 IP 상위 10개를 계산하는 함수
    def top_source_ip_fortigate(self):
        src_ip_counter = Counter()
        for hit in self.log_list:
            log = hit["_source"]
            src_ip = log.get("srcip", "Unknown")
            src_ip_counter[src_ip] += 1
        return dict(
            sorted(src_ip_counter.items(), key=lambda x: x[1], reverse=True)[:10]
        )

    # 목적지 IP 상위 10개를 계산하는 함수
    def top_destination_ip_fortigate(self):
        dst_ip_counter = Counter()
        for hit in self.log_list:
            log = hit["_source"]
            dst_ip = log.get("dstip", "Unknown")
            dst_ip_counter[dst_ip] += 1
        return dict(
            sorted(dst_ip_counter.items(), key=lambda x: x[1], reverse=True)[:10]
        )

    # 장치별 트래픽 계산 함수
    def traffic_by_device_fortigate(self):
        traffic_by_device = defaultdict(int)
        for hit in self.log_list:
            log = hit["_source"]
            device = log.get("devname", "Unknown")  # vd 필드 사용
            sent_byte = float(log.get("sentbyte", 0))  # sentbyte 필드 사용
            rcvd_byte = float(log.get("rcvdbyte", 0))  # rcvdbyte 필드 사용
            if sent_byte + rcvd_byte == 0:
                continue
            traffic_by_device[device] += round(sent_byte / 1000) if sent_byte > 0 else 0
            traffic_by_device[device] += round(rcvd_byte / 1000) if rcvd_byte > 0 else 0
        return dict(sorted(traffic_by_device.items(), key=lambda x: x[1], reverse=True))

    # 사용자별 트래픽 계산 함수
    def traffic_by_user_fortigate(self):
        traffic_by_user = defaultdict(int)
        for hit in self.log_list:
            log = hit["_source"]
            user = log.get("unauthuser", log.get("srcname", "Unknown"))
            sent_byte = int(log.get("sentbyte", 0))
            rcvd_byte = int(log.get("rcvdbyte", 0))
            if sent_byte + rcvd_byte == 0:
                continue
            traffic_by_user[user] += round(sent_byte) if sent_byte > 0 else 0
            traffic_by_user[user] += round(rcvd_byte) if rcvd_byte > 0 else 0
        return dict(sorted(traffic_by_user.items(), key=lambda x: x[1], reverse=True))

    # 애플리케이션별 트래픽 계산 함수
    def traffic_by_application_fortigate(self):
        traffic_by_application = defaultdict(int)
        for hit in self.log_list:
            log = hit["_source"]
            app = log.get("app", log.get("service", "Unknown"))
            sent_byte = float(log.get("sentbyte", 0))
            rcvd_byte = float(log.get("rcvdbyte", 0))
            if sent_byte + rcvd_byte == 0:
                continue
            traffic_by_application[app] += (
                round(sent_byte / 1000) if sent_byte > 0 else 0
            )
            traffic_by_application[app] += (
                round(rcvd_byte / 1000) if rcvd_byte > 0 else 0
            )
        return dict(
            sorted(traffic_by_application.items(), key=lambda x: x[1], reverse=True)
        )

    # 인터페이스별 트래픽 계산 함수
    def traffic_by_interface_fortigate(self):
        traffic_by_interface = defaultdict(int)
        for hit in self.log_list:
            log = hit["_source"]
            srcintf = log.get("srcintf", "Unknown")
            dstintf = log.get("dstintf", "Unknown")
            sent_byte = float(log.get("sentbyte", 0))
            rcvd_byte = float(log.get("rcvdbyte", 0))
            if sent_byte + rcvd_byte == 0:
                continue
            traffic_by_interface[srcintf] += round(sent_byte) if sent_byte > 0 else 0
            traffic_by_interface[dstintf] += round(rcvd_byte) if rcvd_byte > 0 else 0
        return dict(
            sorted(traffic_by_interface.items(), key=lambda x: x[1], reverse=True)
        )

    # 이벤트 수 계산 함수
    def event_counts_fortigate(self):
        event_counts = Counter()
        notable_events = Counter()
        latest_events = []
        for hit in self.log_list:
            log = hit["_source"]
            # date와 time 필드를 결합하여 timestamp 생성
            timestamp = f"{log.get('date')}T{log.get('time')}"  # date와 time 필드 사용
            if timestamp and timestamp != "Unknown":
                try:
                    event_time = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
                    time_key = event_time.strftime("%Y-%m-%d %H:%M")
                except ValueError:
                    print(f"Skipping log with invalid timestamp: {timestamp}")
                    time_key = "Unknown"
            else:
                time_key = "Unknown"

            event_counts[time_key] += 1
            action = log.get("action", "Unknown")  # action 필드 사용
            notable_events[action] += 1

            latest_events.append(
                {
                    "Time": timestamp,
                    "Device": log.get("devname", "Unknown"),  # srcintf 필드 사용
                    "Virtual_Domain": log.get("vd", "Unknown"),  # vd 필드 사용
                    "Subtype": log.get("subtype", "Unknown"),  # subtype 필드 사용
                    "Level": log.get("level", "Unknown"),  # level 필드 사용
                    "Action": action,
                    "Message": log.get("msg", "Unknown"),  # msg 필드 사용
                }
            )

        return (
            dict(sorted(event_counts.items(), key=lambda x: x[0], reverse=False)),
            dict(sorted(notable_events.items(), key=lambda x: x[1], reverse=True)),
            latest_events[:10],
        )

    def give_colors(self, _list: list):
        color_list = ["#24B6D4", "#1cc88a", "#f6c23e", "#fd7e14", "#e74a3b"]
        return [color_list[int(i % 5)] for i in range(len(_list))]
