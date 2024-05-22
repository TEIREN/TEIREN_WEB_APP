from elasticsearch import Elasticsearch
import json

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
    result = es.search(index='test_fortigate_syslog', body=query, size=300)  
    
    # 위험 수준별 로그 리스트 초기화
    high_risk_logs = []
    medium_risk_logs = []
    low_risk_logs = []

    # 이벤트 유형별 필터링을 위한 딕셔너리 초기화
    event_type_logs = {}

    # IP 주소별 필터링을 위한 딕셔너리 초기화
    ip_address_logs = {}

    # 애플리케이션 카테고리별 필터링을 위한 딕셔너리 초기화
    app_category_logs = {}

    # 트래픽 유형별 필터링을 위한 딕셔너리 초기화
    traffic_type_logs = {}

    # 프로토콜별 필터링을 위한 딕셔너리 초기화
    protocol_logs = {}

    # 세션 ID별 필터링을 위한 딕셔너리 초기화
    session_id_logs = {}

    # 서비스별 필터링을 위한 딕셔너리 초기화
    service_logs = {}

    # 전송 및 수신 바이트, 패킷 수에 따른 필터링을 위한 변수 초기화
    sent_byte_threshold = 1000
    rcvd_byte_threshold = 1000
    sent_pkt_threshold = 3
    rcvd_pkt_threshold = 3

    # 트랜잭션 처리 방식에 따른 필터링을 위한 딕셔너리 초기화
    trandisp_logs = {}

    # 검색 결과에서 각 로그를 처리
    for hit in result['hits']['hits']:
        log = hit['_source']

        # 위험 수준별 필터링
        risk_level = log.get('level')
        if risk_level:
            if risk_level == 'critical' or risk_level == 'high':
                high_risk_logs.append(log)
            elif risk_level == 'medium':
                medium_risk_logs.append(log)
            elif risk_level == 'notice' or risk_level == 'informational' or risk_level == 'low':
                low_risk_logs.append(log)

        # 이벤트 유형별 필터링
        event_type = log.get('subtype')
        if event_type:
            if event_type not in event_type_logs:
                event_type_logs[event_type] = []
            event_type_logs[event_type].append(log)

        # IP 주소별 필터링
        src_ip = log.get('srcip')
        dst_ip = log.get('dstip')
        if src_ip:
            if src_ip not in ip_address_logs:
                ip_address_logs[src_ip] = []
            ip_address_logs[src_ip].append(log)
        if dst_ip:
            if dst_ip not in ip_address_logs:
                ip_address_logs[dst_ip] = []
            ip_address_logs[dst_ip].append(log)

        # 애플리케이션 카테고리별 필터링
        app_category = log.get('appcat')
        if app_category:
            if app_category not in app_category_logs:
                app_category_logs[app_category] = []
            app_category_logs[app_category].append(log)

        # 트래픽 유형별 필터링
        traffic_type = log.get('type')
        if traffic_type:
            if traffic_type not in traffic_type_logs:
                traffic_type_logs[traffic_type] = []
            traffic_type_logs[traffic_type].append(log)

        # 프로토콜별 필터링
        protocol = log.get('proto')
        if protocol:
            if protocol not in protocol_logs:
                protocol_logs[protocol] = []
            protocol_logs[protocol].append(log)

        # 세션 ID별 필터링
        session_id = log.get('sessionid')
        if session_id:
            if session_id not in session_id_logs:
                session_id_logs[session_id] = []
            session_id_logs[session_id].append(log)

        # 서비스별 필터링
        service = log.get('service')
        if service:
            if service not in service_logs:
                service_logs[service] = []
            service_logs[service].append(log)

        # 전송 및 수신 바이트, 패킷 수에 따른 필터링
        sent_byte = int(log.get('sentbyte', 0))
        rcvd_byte = int(log.get('rcvdbyte', 0))
        sent_pkt = int(log.get('sentpkt', 0))
        rcvd_pkt = int(log.get('rcvdpkt', 0))
        if sent_byte > sent_byte_threshold or rcvd_byte > rcvd_byte_threshold or \
           sent_pkt > sent_pkt_threshold or rcvd_pkt > rcvd_pkt_threshold:
            # 이런 로그들은 큰 로그 데이터를 가집니다. 이 로그들을 별도로 관리합니다.
            print("Big Log:", json.dumps(log, indent=4))

        # 트랜잭션 처리 방식에 따른 필터링
        trandisp = log.get('trandisp')
        if trandisp:
            if trandisp not in trandisp_logs:
                trandisp_logs[trandisp] = []
            trandisp_logs[trandisp].append(log)

    # 필터링된 로그 수 출력
    print(f"High Risk Logs: {len(high_risk_logs)}개")
    print(f"Medium Risk Logs: {len(medium_risk_logs)}개")
    print(f"Low Risk Logs: {len(low_risk_logs)}개")
    
    print("\n이벤트 유형별 로그 수:")
    for key, value in event_type_logs.items():
        print(f"{key}: {len(value)}개")
    
    print("\nIP 주소별 로그 수:")
    for key, value in ip_address_logs.items():
        print(f"{key}: {len(value)}개")
    
    print("\n애플리케이션 카테고리별 로그 수:")
    for key, value in app_category_logs.items():
        print(f"{key}: {len(value)}개")

    print("\n트래픽 유형별 로그 수:")
    for key, value in traffic_type_logs.items():
        print(f"{key}: {len(value)}개")

    print("\n프로토콜별 로그 수:")
    for key, value in protocol_logs.items():
        print(f"{key}: {len(value)}개")

    print("\n세션 ID별 로그 수:")
    for key, value in session_id_logs.items():
        print(f"{key}: {len(value)}개")

    print("\n서비스별 로그 수:")
    for key, value in service_logs.items():
        print(f"{key}: {len(value)}개")

    print("\n트랜잭션 처리 방식별 로그 수:")
    for key, value in trandisp_logs.items():
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
