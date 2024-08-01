import json
from elasticsearch import Elasticsearch

ELASTICSEARCH_URL = 'http://3.35.81.217:9200'

es = Elasticsearch(ELASTICSEARCH_URL)

def move_to_new_fortigate_index(log_list):
    for log in log_list:
        log['_source']['message']
    es.index(index='finevo_fortigate_syslog', )
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

    # 모든 문서 가져오기
    while len(response['hits']['hits']):
        # 문서 처리 (예: 출력)
        for doc in documents:
            print(doc['_source'])
            print('============'*10)

        # 다음 스크롤 요청
        response = es.scroll(scroll_id=scroll_id, scroll='2m')

        # 다음 스크롤 ID 및 문서 리스트 업데이트
        scroll_id = response['_scroll_id']
        documents = response['hits']['hits']

    # 스크롤 세션 종료
    es.clear_scroll(scroll_id=scroll_id)