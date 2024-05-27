from elasticsearch import Elasticsearch

# Elasticsearch 클라이언트를 설정합니다.
es = Elasticsearch(hosts=["http://3.35.81.217:9200"])

# 룰셋 인덱스 이름 매핑
ruleset_mapping = {
    1: "linux_ruleset",
    2: "window_ruleset",
    3: "genian_ruleset",
    4: "fortigate_ruleset"
}

# detected log 인덱스 이름 매핑
detected_log_mapping = {
    1: "linux_detected_log",
    2: "window_detected_log",
    3: "genian_detected_log",
    4: "fortigate_detected_log"
}

def create_index(index_name: str):
    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name)

# 초기 인덱스 설정 (없을 경우)
for index_name in list(ruleset_mapping.values()) + list(detected_log_mapping.values()):
    create_index(index_name)

print("All indices created successfully.")
