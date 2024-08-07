import json
from elasticsearch import Elasticsearch

ELASTICSEARCH_URL = "http://localhost:9200"

es = Elasticsearch(ELASTICSEARCH_URL)


def move_to_new_index(new_index_name, log_list):
    for log in log_list:
        # if 'message' in log['_source']:
        #     log = fortigate_parse(log['_source']['message'])
        # print(log['_source'])
        log = log['_source']
        es.index(index=new_index_name, document=log)


def move_index(og_index_name, new_index_name):
    # 스크롤을 사용하여 모든 문서 가져오기
    scroll_size = 1000  # 한 번에 가져올 문서 수
    response = es.search(
        index=og_index_name,
        body={"query": {"match_all": {}}},
        scroll="2m",  # 스크롤 유지 시간
        size=scroll_size,
    )

    # 초기 스크롤 ID 및 문서 리스트
    scroll_id = response["_scroll_id"]
    documents = response["hits"]["hits"]
    print(response["hits"]["total"]["value"])
    # 모든 문서 가져오기
    while len(response["hits"]["hits"]):
        # 문서 처리 (예: 출력)
        move_to_new_index(new_index_name=new_index_name,log_list=documents)
        break

        # 다음 스크롤 요청
        response = es.scroll(scroll_id=scroll_id, scroll="2m")

        # 다음 스크롤 ID 및 문서 리스트 업데이트
        scroll_id = response["_scroll_id"]
        documents = response["hits"]["hits"]
    # 스크롤 세션 종료
    es.clear_scroll(scroll_id=scroll_id)
    print("index moved successfully.")


if __name__ == "__main__":
    # move_index('og_index_name', 'new_index_name')
    move_index(
        og_index_name="test_finevo_genian_syslog",
        new_index_name="genian_syslog",
    )
