import json
from elasticsearch import Elasticsearch

ELASTICSEARCH_URL = 'http://3.35.81.217:9200'

es = Elasticsearch(ELASTICSEARCH_URL)

def move_to_new_fortigate_index(log_list):
    for log in log_list:
        if 'message' in log['_source']:
            # print("="*50)
            log = fortigate_parse(log['_source']['message'])
            # print("="*50)
            es.index(index='finevo_fortigate_syslog', document=log)

def fortigate_parse(log: str):
    clean_log = log[log.find('>') + 1:].strip()
    log_dict = {}
    items = []
    current_item = []
    in_quotes = False

    for char in clean_log:
        if char == '\"':
            in_quotes = not in_quotes
        if char == ' ' and not in_quotes:
            if current_item:
                items.append(''.join(current_item))
                current_item = []
        else:
            current_item.append(char)

    if current_item:
        items.append(''.join(current_item))

    for item in items:
        if '=' in item:
            key, value = item.split('=', 1)
            value = value.strip().strip('"')

            # 'srcswversion' 필드의 경우 특별한 처리
            if key == 'srcswversion':
                log_dict[key] = value  # 문자열로 저장
            elif value.isdigit():
                log_dict[key] = int(value)  # 숫자로 변환
            else:
                log_dict[key] = value  # 기타 문자열로 저장

    return log_dict

def renew_fortigate(request):
    index_name = 'test_finevo_fortigate_syslog'  # 검색할 인덱스 이름

    # 스크롤을 사용하여 모든 문서 가져오기
    scroll_size = 1000  # 한 번에 가져올 문서 수
    response = es.search(
        index=index_name,
        body={
            "query": {
                "match_all": {}
            }
        },
        scroll='2m',  # 스크롤 유지 시간
        size=scroll_size
    )

    # 초기 스크롤 ID 및 문서 리스트
    scroll_id = response['_scroll_id']
    documents = response['hits']['hits']
    print(response['hits']['total']['value'])
    cnt = 0
    # 모든 문서 가져오기
    while len(response['hits']['hits']):
        # 문서 처리 (예: 출력)
        move_to_new_fortigate_index(log_list=documents)
        # break
    
        # 다음 스크롤 요청
        response = es.scroll(scroll_id=scroll_id, scroll='2m')

        # 다음 스크롤 ID 및 문서 리스트 업데이트
        scroll_id = response['_scroll_id']
        documents = response['hits']['hits']
    print(cnt)
    # 스크롤 세션 종료
    es.clear_scroll(scroll_id=scroll_id)