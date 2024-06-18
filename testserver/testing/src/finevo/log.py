import json
import logging
from .tableProperty import get_property_key
from django.core.paginator import Paginator
from django.shortcuts import render
from django.http import JsonResponse
from elasticsearch import Elasticsearch, ConnectionError

# Elasticsearch 클라이언트를 설정합니다.
es = Elasticsearch(hosts=["http://3.35.81.217:9200/"])


# 로그 관리 클래스
class LogManagement():
    def __init__(self, system: str, page: int):
        self.es = Elasticsearch("http://3.35.81.217:9200/")  # Elasticsearch 연결
        self.system = system
        self.query = {"match_all": {}}  # 기본 쿼리 설정
        self.page_number = page
        self.timestamp = self.get_timestamp()
        
    def get_timestamp(self):
        timestamp_mapping = {
            "linux": "@timestamp",
            "genian": "@timestamp",
            "window": "date",
            "fortigate": "eventtime",
        }
        return timestamp_mapping[self.system]
        
    # 로그 검색 함수
    def search_logs(self):
        try:
            self.es.indices.put_settings(index=f"test_{self.system}_syslog", body={"index.max_result_window": 1000000})
            response = self.es.search(index=f"test_{self.system}_syslog", body={"size": 25,"query": self.query, "sort":{f"{self.timestamp}": "desc"}, "from":((self.page_number-1)*25)})
            hits = response['hits']['hits']
            log_list = []
            for hit in hits:
                log = hit['_source']
                try:
                    detected_response = self.es.search(index=f"{self.system}_detected_log", body={"query":{"bool": {"must": [{"match": {f"{self.timestamp}": hit['_source'][f'{self.timestamp}']}}]}}}, size=1000)
                    if len(detected_response['hits']['hits']) > 0:
                        detected_rules = []
                        severities = []
                        for detect_hit in detected_response['hits']['hits']:
                            detected_rules.append(detect_hit['_source']['detected_by_rule'])
                            rule_info = self.es.search(index= f"{self.system}_ruleset", body={"query":{"bool": {"must": [{"match": {"name": detect_hit['_source']['detected_by_rule']}}]}}})
                            severities.append(rule_info['hits']['hits'][0]['_source']['severity'])
                        log['detected_by_rules'] = detected_rules
                        log['severities'] = severities
                except Exception as e:
                    logging.error(f"Error searching logs: {e}")
                finally:
                    log_list.append(log)
            total_count = self.es.count(index=f"test_{self.system}_syslog", query=self.query)['count']
            self.total_page = int(round(total_count/25, 0))
        except Exception as e:
            total_count = 0
            log_list = []
            self.total_page = 1
            logging.error(f"Error searching logs: {e}")
        return total_count, log_list

    # 쿼리 문자열을 파싱하는 함수
    def parse_query_string(self, query_string):
        must_conditions = []
        must_not_conditions = []
        filters = {}

        conditions = query_string.split('&')
        for condition in conditions:
            condition = condition.strip()
            if '!=' in condition:
                key, value = map(str.strip, condition.split('!='))  # NOT 조건 파싱
                must_not_conditions.append({"match": {key: value}})
                filters[f"NOT_{key}"] = [value]
            else:
                key, value = map(str.strip, condition.split(':'))  # AND 조건 파싱
                must_conditions.append({"match": {key: value}})
                filters[key] = [value]

        return must_conditions, must_not_conditions, filters


    """
    AND 조건 쿼리: 시설이 daemon이고 심각도가 warning인 로그를 검색하는 쿼리:


    facility: daemon & severity: warning

    NOT 조건 쿼리: 시설이 daemon이 아니고 심각도가 warning인 로그를 검색하는 쿼리:


    facility != daemon & severity: warning

    복합 조건 쿼리: 시설이 daemon이고 심각도가 warning이며 애플리케이션이 nginx가 아닌 로그를 검색하는 쿼리:


    facility: daemon & severity: warning & application != nginx

    """
    # 필터링된 쿼리 함수
    def filter_query(self, filters):
        must_conditions = []
        must_not_conditions = []
        parsed_filters = {}

        for key, values in filters.items():
            if key in ["page", "csrfmiddlewaretoken"]:
                continue
            if not isinstance(values, list):
                values = [values]

            for value in values:
                if '&' in value or '!=' in value:
                    parsed_must, parsed_must_not, parsed_filter = self.parse_query_string(value)
                    must_conditions.extend(parsed_must)
                    must_not_conditions.extend(parsed_must_not)
                    parsed_filters.update(parsed_filter)
                else:
                    if key.startswith("NOT_"):  # NOT 조건 처리
                        field = key[4:]
                        should_conditions = [{"match": {field: v}} for v in values]
                        must_not_conditions.append({"bool": {"should": should_conditions, "minimum_should_match": 1}})
                    else:  # 기본 AND 조건 처리
                        must_conditions.append({"match": {key: value}})
                        parsed_filters[key] = values

        if must_conditions or must_not_conditions:
            self.query = {
                "bool": {
                    "must": must_conditions,
                    "must_not": must_not_conditions
                }
            }
        else:
            self.query = {"match_all": {}}

        logging.debug(f"Constructed Bool Query: {json.dumps(self.query, indent=4)}")
        logging.debug(f"Filters Applied: {parsed_filters}")
        return self.search_logs()

    # 페이지네이션 적용 함수
    def paginate_logs(self, log_list, page_number, logs_per_page=25):
        paginator = Paginator(log_list, logs_per_page)
        page_obj = paginator.get_page(page_number)
        return page_obj
    
    def paginate(self):
        #page_range
        start_page = max(int(self.page_number)-5, 1)
        end_page = min(int(self.page_number)+5, self.total_page)
        page_range = range(start_page, end_page+1)

        
        return {
            'has_previous': False if self.page_number == 1 else True,
            'has_next': False if self.page_number == self.total_page else True,
            'previous_page_number': self.page_number-1,
            'next_page_number': self.page_number+1,
            'page_range': page_range,
            'number': self.page_number,
            'num_pages': self.total_page
        }
        
    # 로그 속성 추출 함수
    def fetch_log_properties(self):
        query = {
            "query": {
                "match_all": {}
            },
            "size": 10000
        }
        
        response = self.es.search(index=f"test_{self.system}_syslog", body=query)
        hits = response['hits']['hits']
        
        exclude_keys = {'@timestamp', 'message', 'timegenerated', '@version', 'date', 'eventtime','teiren_@timestamp', 'teiren_ddd', 'teiren_timestamp'} # 제외할 로그 프라퍼티
        
        properties = {}
        for hit in hits:
            log = hit['_source']
            for key, value in log.items():
                if key not in exclude_keys and value is not None and value != '':
                    if key not in properties:
                        properties[key] = set()
                    if isinstance(value, (str, int, float, bool)):
                        properties[key].add(value)
    
        properties_list = [{key: list(values)} for key, values in properties.items()]
        
        return properties_list


# 시스템 로그 리스트를 보여주는 함수
def list_logs(request, system):
    # logging.basicConfig(level=logging.DEBUG)
    page_number = int(request.GET.get('page', 1))
    system_log = LogManagement(system=system, page=page_number)    
    filters = dict(request.GET)
    if 'page' in filters:
        del filters['page']
    if filters:
        total_count, log_list = system_log.filter_query(filters)
    # 필터 쿼리가 있는 경우 필터링된 로그만 검색
    elif 'query' in filters:
        query_string = filters.pop('query')[0]
        parsed_must, parsed_must_not, parsed_filters = system_log.parse_query_string(query_string)
        filters.update(parsed_filters)
        total_count, log_list = system_log.filter_query(filters)
    else:
        total_count, log_list = system_log.search_logs()

    # Ajax 요청 처리: Ajax 요청인 경우, 필터링된 로그 리스트와 기타 정보를 JsonResponse로 반환
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Apply pagination
        page_obj = system_log.paginate()
        context = {
            'total_count': total_count,
            'log_list': log_list,
            'page_obj': page_obj,
            'page': page_obj['number'],
            'system': system.title(),
            'table_properties': get_property_key(system)
        }
        return render(request, 'testing/finevo/log_table.html', context=context)

    # 룰셋을 기반으로 로그를 탐지합니다.
    try:
        context = {
            'total_count': total_count,
            'log_list': log_list,
            'page_obj': system_log.paginate(),
            'system': system.title(),
            'page': page_number,
            'log_properties': system_log.fetch_log_properties(), # 로그 프로퍼티 추출
            'table_properties': get_property_key(system)
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

        res = es.search(index=f"{system}_ruleset", body={"query": {"match": {"name": ruleset_name}}})
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
        system_log = LogManagement(system=system, page=page_number)
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