import json
import logging
from django.core.paginator import Paginator
from django.shortcuts import render
from django.http import JsonResponse
from elasticsearch import Elasticsearch, ConnectionError

# Elasticsearch 클라이언트를 설정합니다.
es = Elasticsearch(hosts=["http://3.35.81.217:9200/"])

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
            response = self.es.search(index=f"test_{self.system}_syslog", scroll='1m', body={"query": self.query}, size=10000)
            log_list = [hit['_source'] for hit in response['hits']['hits']]
            total_count = response['hits']['total']['value']
        except Exception as e:
            total_count = 0
            log_list = []
            logging.error(f"Error searching logs: {e}")
        return total_count, log_list

    # 필터링된 쿼리 함수
    def filter_query(self, filters):
        must_conditions = []

        for key, values in filters.items():
            if key in ["page", "csrfmiddlewaretoken"]:
                continue
            if not isinstance(values, list):
                values = [values]
            should_conditions = [{"match": {key: value}} for value in values]
            must_conditions.append({"bool": {"should": should_conditions, "minimum_should_match": 1}})

        if must_conditions:
            self.query = {
                "bool": {
                    "must": must_conditions
                }
            }
        else:
            self.query = {"match_all": {}}

        logging.debug(f"Constructed Bool Query: {json.dumps(self.query, indent=4)}")
        logging.debug(f"Filters Applied: {filters}")
        return self.search_logs()

    # 페이지네이션 적용 함수
    def paginate_logs(self, log_list, page_number, logs_per_page=25):  # 변경된 로그 수
        paginator = Paginator(log_list, logs_per_page)
        page_obj = paginator.get_page(page_number)
        return page_obj
    
    # 로그 속성 추출 함수
    def fetch_log_properties(self, exclude_keys=set()):
        query = {
            "query": {
                "match_all": {}
            },
            "size": 1000
        }
        
        response = self.es.search(index=f"test_{self.system}_syslog", body=query)
        hits = response['hits']['hits']
        
        exclude_keys = {'@timestamp', 'message', 'timegenerated', '@version'} # 제외할 로그 프라퍼티
        
        properties = {}
        for hit in hits:
            log = hit['_source']
            for key, value in log.items():
                if key not in exclude_keys:
                    if key not in properties:
                        properties[key] = set()
                    if isinstance(value, (str, int, float, bool)): 
                        properties[key].add(value)
    
        properties_list = [{key: list(values)} for key, values in properties.items()]
        
        return properties_list


# 시스템 로그 리스트를 보여주는 함수
def list_logs(request, system):
    logging.basicConfig(level=logging.DEBUG)
    system_log = LogManagement(system=system)
    
    page_number = int(request.GET.get('page', 1))
    
    filters = dict(request.GET)
    
    if filters:
        total_count, log_list = system_log.filter_query(filters)
    else:
        total_count, log_list = system_log.search_logs()

    # Apply pagination
    page_obj = system_log.paginate_logs(log_list, page_number)

    # Ajax 요청 처리: Ajax 요청인 경우, 필터링된 로그 리스트와 기타 정보를 JsonResponse로 반환
    if request.is_ajax():
        return JsonResponse({
            'total_count': total_count,
            'log_list': [log for log in page_obj.object_list],
            'page_obj': {
                'number': page_obj.number,
                'has_previous': page_obj.has_previous(),
                'has_next': page_obj.has_next(),
                'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
                'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
                'paginator': {
                    'num_pages': page_obj.paginator.num_pages
                }
            }
        })

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

        # Apply pagination to combined log list
        combined_page_obj = system_log.paginate_logs(all_logs, page_number)

        # 로그 프로퍼티 추출
        log_properties = system_log.fetch_log_properties()
        
        context = {
            'total_count': len(all_logs),
            'log_list': combined_page_obj.object_list,
            'page_obj': combined_page_obj,
            'system': system.title(),
            'page': page_number,
            'log_properties': log_properties
        }

        return render(request, 'testing/finevo/elasticsearch.html', context=context)

    except ConnectionError as e:
        logging.error(f"Connection error: {e}")
        context = {
            'total_count': 0,
            'log_list': [],
            'page_obj': None,
            'system': system.title(),
            'page': page_number,
            'log_properties': []
        }
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        context = {
            'total_count': 0,
            'log_list': [],
            'page_obj': None,
            'system': system.title(),
            'page': page_number,
            'log_properties': []
        }

    return render(request, 'testing/finevo/elasticsearch.html', context=context)

# 룰셋에 따른 로그 리스트를 보여주는 함수
def logs_by_ruleset(request, system, ruleset_name):
    try:
        page_number = request.GET.get('page', 1)

        ruleset_index = ruleset_mapping[list(log_index.keys())[list(log_index.values()).index(f"test_{system}_syslog")]]
        res = es.search(index=ruleset_index, body={"query": {"match": {"name": ruleset_name}}})
        if res['hits']['total']['value'] == 0:
            return render(request, 'testing/finevo/error_page.html', {'error': f"No ruleset found with name {ruleset_name}"})
        
        rule = res['hits']['hits'][0]['_source']
        rule_query = rule["query"]["query"]

        log_res = es.search(index=f"test_{system}_syslog", body={"query": rule_query, "size": 10000})
        log_list = [hit['_source'] for hit in log_res['hits']['hits']]

        # 각 로그 항목에 detected_by_rules 필드를 추가
        for log in log_list:
            log['detected_by_rules'] = [ruleset_name]
        
        log_list.sort(key=lambda x: x.get('@timestamp', x.get('timestamp', '')))

        # Apply pagination
        system_log = LogManagement(system=system)
        page_obj = system_log.paginate_logs(log_list, page_number)

        context = {
            'total_count': len(log_list),
            'log_list': page_obj.object_list,
            'page_obj': page_obj,
            'system': system.title(),
            'ruleset_name': ruleset_name,
            'page': page_number,
            'ruleset': json.dumps(rule, indent=4)  # 룰셋 세부 정보를 prettified JSON으로 추가
        }
        return render(request, 'testing/finevo/logs_by_ruleset.html', context=context)

    except ConnectionError as e:
        return JsonResponse({"error": f"Connection error: {e}"}, status=500)
    except Exception as e:
        return JsonResponse({"error": f"An error occurred: {e}"}, status=500)
