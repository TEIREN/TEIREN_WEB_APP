from elasticsearch import Elasticsearch
import json
from datetime import datetime

# Elasticsearch 서버 URL 설정
ELASTICSEARCH_URL = 'http://localhost:9200'
# Elasticsearch 인스턴스 생성
es = Elasticsearch(ELASTICSEARCH_URL)

def search_logs(start_time=None, end_time=None):
    # 쿼리 조건 생성
    query = {
        "query": {
            "bool": {
                "must": []
            }
        }
    }
    
    if start_time and end_time:
        # 시간 범위가 주어진 경우 쿼리에 시간 조건 추가
        query["query"]["bool"]["must"].append({
            "range": {
                "@timestamp": {
                    "gte": start_time,
                    "lte": end_time,
                    "format": "yyyy-MM-dd'T'HH:mm:ss.SSSSSS"
                }
            }
        })

    # Elasticsearch에서 쿼리 실행
    result = es.search(index='test_linux_syslog', body=query, size=10000)  
    
    # 로그를 출력하기 위한 리스트 초기화
    logs = []

    # 검색 결과에서 각 로그를 처리하면서 JSON 형식으로 파싱하여 리스트에 추가
    for hit in result['hits']['hits']:
        log = hit['_source']
        logs.append(json.dumps(log, indent=4, ensure_ascii=False))

    # 로그 출력
    print("\n검색된 로그:")
    for log in logs:
        print(log)

    # 소스 IP 주소별 사용 횟수를 저장할 딕셔너리 초기화
    ip_count = {}

    # 검색 결과에서 각 로그를 처리
    for hit in result['hits']['hits']:
        log = hit['_source']

        # teiren_request_ip 필드 추출
        teiren_ip = log.get('teiren_request_ip')
        if teiren_ip:
            ip_count[teiren_ip] = ip_count.get(teiren_ip, 0) + 1

    # 각 IP 주소별 사용 횟수 출력
    print("\nIP 주소별 사용 횟수:")
    for ip, count in ip_count.items():
        print(f"{ip}: {count}번")

    # 필터링 조건별 로그 수를 저장할 딕셔너리 초기화
    severity_logs = {}
    facility_logs = {}
    programname_logs = {}

    # 검색 결과에서 각 로그를 처리
    for hit in result['hits']['hits']:
        log = hit['_source']

        # 심각도별 필터링
        severity = log.get('severity')
        if severity:
            if severity not in severity_logs:
                severity_logs[severity] = 0
            severity_logs[severity] += 1

        # 시설별 필터링
        facility = log.get('facility')
        if facility:
            if facility not in facility_logs:
                facility_logs[facility] = 0
            facility_logs[facility] += 1

        # 프로그램 이름별 필터링
        programname = log.get('programname')
        if programname:
            if programname not in programname_logs:
                programname_logs[programname] = 0
            programname_logs[programname] += 1

    # 각 필터링 조건별 로그 수 출력
    print("\n심각도별 로그 수:")
    for key, value in severity_logs.items():
        print(f"{key}: {value}개")
    
    print("\n시설별 로그 수:")
    for key, value in facility_logs.items():
        print(f"{key}: {value}개")
    
    print("\n프로그램 이름별 로그 수:")
    for key, value in programname_logs.items():
        print(f"{key}: {value}개")

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
