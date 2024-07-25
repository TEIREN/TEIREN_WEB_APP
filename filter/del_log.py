from elasticsearch import Elasticsearch

# Elasticsearch 클라이언트 생성
es = Elasticsearch(hosts=["http://3.35.81.217:9200/"])
# 삭제 쿼리 정의
delete_query = {
    "query": {
        "bool": {
            "must": [
                {"match": {"teiren_request_ip": "3.35.81.217"}},
            ]
        }
    }
}

# delete_by_query API 호출
response = es.delete_by_query(index='test_linux_syslog', body=delete_query)

print(response)
