from elasticsearch import Elasticsearch

# Elasticsearch 클라이언트 생성
es = Elasticsearch(hosts=["http://3.35.81.217:9200/"])
# 삭제 쿼리 정의
delete_query = {
    "query": {
        "bool": {
            "must": [
                # {"match": {"SYSTEM": "mysql"}},
                {'match': {"TAG_NAME": "sql_tag"}},
            ]
        }
    }
}

# delete_by_query API 호출
# response = es.delete_by_query(index='integration_info', body=delete_query)
response = es.delete_by_query(index='mysql_syslog', body=delete_query)


print(response)
