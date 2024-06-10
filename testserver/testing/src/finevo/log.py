import json
from django.shortcuts import render
from django.http import JsonResponse
from elasticsearch import Elasticsearch, ConnectionError

# Elasticsearch 클라이언트를 설정합니다.
es = Elasticsearch(hosts=["http://3.35.81.217:9200"])

# 탐지 대상 로그 인덱스
log_index = {
    1: "test_linux_syslog",
    2: "test_window_syslog",
    3: "test_genian_syslog",
    4: "test_fortigate_syslog"
}

# 룰셋 인덱스 이름 매핑
ruleset_mapping = {
    1: "linux_ruleset",
    2: "window_ruleset",
    3: "genian_ruleset",
    4: "fortigate_ruleset"
}

# 로그 관리 클래스
class LogManagement():
    def __init__(self, system: str):
        self.es = Elasticsearch("http://3.35.81.217:9200/")  # Elasticsearch 연결
        self.system = system
        self.query = {"match_all": {}}  # 기본 쿼리 설정
    
    # 로그 검색 함수
    def search_logs(self):
        try:
            response = self.es.search(index=f"test_{self.system}_syslog", scroll='1m', body={"query": self.query}, size=1000)
            log_list = [hit['_source'] for hit in response['hits']['hits']]
            total_count = response['hits']['total']['value']
        except Exception as e:
            total_count = 0
            log_list = []
            print(f"Error searching logs: {e}")
        return total_count, log_list

    # 필터링된 쿼리 함수
    def filter_query(self, query):
        page = query.pop('page') if 'page' in query else 'no page'
        for clause in query:
            try:
                new_clause = json.loads(query[clause].replace("'", '"'))
            except Exception as e:
                new_clause = []
                print(f"Error parsing query clause: {e}")
            finally:
                query[clause] = new_clause
        if 'should' in query and len(query['should']) != 0:
            query.update({"minimum_should_match": 1})
        self.query = {
            "bool": query
        }
        return self.search_logs()

# 시스템 로그 리스트를 보여주는 함수
def list_logs(request, system):
    system_log = LogManagement(system=system)
    total_count, log_list = system_log.search_logs()

    # 룰셋을 기반으로 로그를 탐지합니다.
    index_choice = list(log_index.keys())[list(log_index.values()).index(f"test_{system}_syslog")]
    ruleset_index = ruleset_mapping[index_choice]
    
    try:
        res = es.search(index=ruleset_index, body={"query": {"match_all": {}}, "size": 10000})
        rulesets = res['hits']['hits']
        logs_detected = {}

        for rule in rulesets:
            rule_query = rule["_source"]["query"]["query"]
            rule_name = rule["_source"]["name"]
            severity = rule["_source"]["severity"]

            log_res = es.search(index=f"test_{system}_syslog", body={"query": rule_query, "size": 10000})
            logs_found = log_res['hits']['total']['value']

            if logs_found > 0:
                for log in log_res['hits']['hits']:
                    log_id = log["_id"]
                    log_doc = log["_source"]

                    if log_id not in logs_detected:
                        logs_detected[log_id] = log_doc
                        logs_detected[log_id]["detected_by_rules"] = []
                        logs_detected[log_id]["severities"] = []

                    logs_detected[log_id]["detected_by_rules"].append(rule_name)
                    logs_detected[log_id]["severities"].append(severity)

        detected_log_list = list(logs_detected.values())
        all_logs = log_list + detected_log_list
        all_logs.sort(key=lambda x: x.get('@timestamp', x.get('timestamp', '')))

        context = {
            'total_count': len(all_logs),
            'log_list': all_logs,
            'system': system.title(),
            'page': 1
        }

    except ConnectionError as e:
        print(f"Connection error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

    return render(request, 'testing/finevo/elasticsearch.html', context=context)

# 룰셋에 따른 로그 리스트를 보여주는 함수
def logs_by_ruleset(request, system, ruleset_name):
    try:
        ruleset_index = ruleset_mapping[list(log_index.keys())[list(log_index.values()).index(f"test_{system}_syslog")]]
        res = es.search(index=ruleset_index, body={"query": {"match": {"name": ruleset_name}}})
        if res['hits']['total']['value'] == 0:
            return render(request, 'testing/finevo/error_page.html', {'error': f"No ruleset found with name {ruleset_name}"})
        
        rule = res['hits']['hits'][0]['_source']
        rule_query = rule["query"]["query"]

        log_res = es.search(index=f"test_{system}_syslog", body={"query": rule_query, "size": 10000})
        log_list = [hit['_source'] for hit in log_res['hits']['hits']]
        
        log_list.sort(key=lambda x: x.get('@timestamp', x.get('timestamp', '')))

        context = {
            'total_count': len(log_list),
            'log_list': log_list,
            'system': system.title(),
            'ruleset_name': ruleset_name,
            'page': 1
        }
        return render(request, 'testing/finevo/logs_by_ruleset.html', context=context)

    except ConnectionError as e:
        return JsonResponse({"error": f"Connection error: {e}"}, status=500)
    except Exception as e:
        return JsonResponse({"error": f"An error occurred: {e}"}, status=500)
