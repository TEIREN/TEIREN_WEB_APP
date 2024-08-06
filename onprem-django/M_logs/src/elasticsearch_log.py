import json
# import logging
from django.core.paginator import Paginator
from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from elasticsearch import Elasticsearch, ConnectionError, NotFoundError

# Elasticsearch 클라이언트를 설정합니다.
es = Elasticsearch(hosts=["http://3.35.81.217:9200/"])

# Docker 로그에 기록되도록 로깅 설정
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

# 로그 관리 클래스
class LogManagement():
    def __init__(self, system: str, page: int):
        self.es = Elasticsearch("http://3.35.81.217:9200/")  # Elasticsearch 연결
        self.system = system
        self.query = {"match_all": {}}  # 기본 쿼리 설정
        self.page_number = page
        self.timestamp = self.get_timestamp()
        self.limit = 25

    def get_timestamp(self):
        timestamp_mapping = {
            "linux": "@timestamp",
            "genian": "timestamp.keyword",
            "window": "date",
            "fortigate": "eventtime.keyword",
            "mssql": "ID",
            "snmp": ""
        }
        return timestamp_mapping[self.system]
    
    def save_table_property(self, request):
        document = {'system': self.system, 'properties': [property for property in dict(request.GET)['properties'] if property]}
        print(request.GET.get('properties'))
        try:
            es.update_by_query(index="table_property", body={
                "query":{
                    "match": {"system": self.system}
                },
                "script":{
                    "source": f"ctx._source.properties = {document['properties']}",
                    "lang": "painless" 
                }
            })
            return HttpResponse('Successfully Saved')
        except NotFoundError:
            try:
                es.index(index=f"table_property", document=document)
                return HttpResponse('Successfully Saved')
            except Exception as e:
                return HttpResponse(f"error: {e}")
        except ConnectionError as e:
            return HttpResponse(f"Connection error: {e}")
        except Exception as e:
            return HttpResponse(f"An error occurred: {e}")

    def get_property_key(self):
        try:
            response = es.search(index=f"table_property", body={"query": {"match": {'system': self.system}}})
            return response['hits']['hits'][0]['_source']['properties']
        except:
            return []
        
    # 로그 검색 함수
    def search_logs(self):
        try:
            self.es.indices.put_settings(index=f"{self.system}_syslog", body={"index.max_result_window": 1000000})
            try:
                self.es.indices.put_settings(index=f"{self.system}_detected_log", body={"index.max_result_window": 1000000})
            except:
                pass
            response = self.es.search(index=f"{self.system}_syslog", body={"size": self.limit, "query": self.query, "sort": {f"{self.timestamp}": "desc"}, "from": ((self.page_number-1)*self.limit)})
            hits = response['hits']['hits']
            log_list = []
            for hit in hits:
                log = hit['_source']
                try:
                    detected_response = self.es.search(index=f"{self.system}_detected_log", body={"query": {"bool": {"must": [{"match": {f"{self.timestamp}": hit['_source'][f'{self.timestamp}']}}]}}}, size=100000)
                    if len(detected_response['hits']['hits']) > 0:
                        detected_rules = set()  # 중복을 제거하기 위해 set 사용
                        severities = []
                        for detect_hit in detected_response['hits']['hits']:
                            detected_log = detect_hit['_source']
                            if self.is_rule_match(detected_log, log):  # 매칭 조건 확인
                                detected_by_rules = detected_log.get('detected_by_rule', '')
                                if detected_by_rules:
                                    detected_rules.add(detected_by_rules)
                                rule_info = self.es.search(index=f"{self.system}_ruleset", body={"query": {"bool": {"must": [{"match": {"name": detected_by_rules}}]}}})
                                severities.append(rule_info['hits']['hits'][0]['_source']['severity'])
                        log['detected_by_rules'] = list(detected_rules)
                        log['severities'] = severities
                        # logging.debug(f"Log ID: {hit['_id']}, Detected by rules: {log['detected_by_rules']}")  # 디버깅용으로 로그에 기록
                except Exception as e:
                    print(e)
                    # logging.error(f"Error searching logs: {e}")
                finally:
                    log_list.append(log)
            total_count = self.es.count(index=f"{self.system}_syslog", query=self.query)['count']
            self.total_page = int(round(total_count/self.limit, 0))
        except Exception as e:
            total_count = 0
            log_list = []
            self.total_page = 1
            print(e)
            # logging.error(f"Error searching logs: {e}")
        return total_count, log_list
    
    def is_rule_match(self, detected_log, actual_log):
        # 룰셋의 조건이 실제 로그에 맞는지 확인하는 로직 추가
        # 예시: detected_log의 eventtype과 actual_log의 eventtype이 같은지 확인
        match_conditions = detected_log.get(
            "query", {}).get("bool", {}).get("must", [])
        for condition in match_conditions:
            should_conditions = condition.get("bool", {}).get("should", [])
            for should_condition in should_conditions:
                if "match" in should_condition:
                    key, value = list(should_condition["match"].items())[0]
                    if key in actual_log and actual_log[key] != value:
                        return False
                if "bool" in should_condition and "must_not" in should_condition["bool"]:
                    must_not_condition = should_condition["bool"]["must_not"]
                    for key, value in must_not_condition.items():
                        if key in actual_log and actual_log[key] == value:
                            return False
        return True
    
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
                key, value = map(str.strip, condition.split(':'))  # 기본 조건 파싱
                if key not in filters:
                    filters[key] = []
                filters[key].append(value)

        for key, values in filters.items():
            if key.startswith("NOT_"):
                continue
            if len(values) > 1:
                must_conditions.append({
                    "bool": {
                        "should": [{"match": {key: value}} for value in values],
                        "minimum_should_match": 1
                    }
                })
            else:
                must_conditions.append({"match": {key: values[0]}})

        return must_conditions, must_not_conditions, filters

    """
    OR 조건 쿼리 : 

    facility: daemon & facility:user

    AND 조건 쿼리: 

    facility: daemon & severity: warning

    NOT 조건 쿼리: 

    facility != daemon & severity: warning

    복합 조건 쿼리: 

    severity : err & severity : notice & facility != user
    """

    # 필터링된 쿼리 함수
    def filter_query(self, filters):
        must_conditions = []
        must_not_conditions = []
        should_conditions = {}
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
                    else:  # 기본 OR 조건 처리
                        if key not in should_conditions:
                            should_conditions[key] = []
                        should_conditions[key].append({"match": {key: value}})
                        parsed_filters[key] = values

        # should_conditions를 must_conditions로 변환
        for key, conditions in should_conditions.items():
            must_conditions.append({"bool": {"should": conditions, "minimum_should_match": 1}})

        if must_conditions or must_not_conditions:
            self.query = {
                "bool": {
                    "must": must_conditions,
                    "must_not": must_not_conditions
                }
            }
            # print(self.query)
        else:
            self.query = {"match_all": {}}

        # logging.debug(f"Constructed Bool Query: {json.dumps(self.query, indent=4)}")
        # logging.debug(f"Filters Applied: {parsed_filters}")
        return self.search_logs()

    # 페이지네이션 적용 함수
    def paginate_logs(self, log_list, page_number, logs_per_page=25):
        paginator = Paginator(log_list, logs_per_page)
        page_obj = paginator.get_page(page_number)
        return page_obj
    
    def paginate(self):
        #page_range
        if self.total_page == 0:
            self.total_page = 1
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
        
        response = self.es.search(index=f"{self.system}_syslog", body=query)
        hits = response['hits']['hits']
        
        exclude_keys = ['@timestamp', 'message', 'timegenerated', '@version', 'date', 'eventtime','teiren_@timestamp', 'teiren_ddd', 'teiren_timestamp', 'Message', 'TimeGenerated', 'TimeWritten', 'RecordNumber'] # 제외할 로그 프라퍼티
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
def list_logs(request, resource_type, system):
    # logging.basicConfig(level=logging.DEBUG)
    if system == 'fortinet':
        system = 'fortigate'
    elif system == 'genians':
        system = 'genian'
    page_number = int(request.GET.get('page', 1))
    system_log = LogManagement(system=system, page=page_number)    
    filters = dict(request.GET)
    if 'page' in filters:
        del filters['page']
        # print('1'*50)
    if 'query' in filters and filters['query'][0] == '':
        del filters['query']
        # print('2'*50)
    if 'query' not in filters:
        total_count, log_list = system_log.filter_query(filters)
        # print('3'*50)
    # 필터 쿼리가 있는 경우 필터링된 로그만 검색
    elif 'query' in filters:
        query_string = filters.pop('query')[0]
        parsed_must, parsed_must_not, parsed_filters = system_log.parse_query_string(query_string)
        filters.update(parsed_filters)
        
        total_count, log_list = system_log.filter_query(filters)
        # print('4'*50)
    else:
        total_count, log_list = system_log.search_logs()
        # print('5'*50)

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
            'resource_type': resource_type,
            'table_properties': system_log.get_property_key()
        }
        # print('6'*50)
        return render(request, 'M_logs/elasticsearch/log_table.html', context=context)

    # 룰셋을 기반으로 로그를 탐지합니다.
    try:
        # print('7'*50)
        context = {
            'total_count': total_count,
            'log_list': log_list,
            'page_obj': system_log.paginate(),
            'system': system.title(),
            'resource_type': resource_type,
            'page': page_number,
            'log_properties': system_log.fetch_log_properties(), # 로그 프로퍼티 추출
            'table_properties': system_log.get_property_key()
        }
        # for i in log_list:
        #     print(i)
        #     print('#'*50)
        #     print('\n')
        # print('8'*50)
        return context

    except ConnectionError as e:
        # logging.error(f"Connection error: {e}")
        context = {
            'total_count': 0,
            'log_list': [],
            'page_obj': None,
            'system': system.title(),
            'resource_type': resource_type,
            'page': page_number,
            'log_properties': []
        }
    except Exception as e:
        # logging.error(f"An error occurred: {e}")
        context = {
            'total_count': 0,
            'log_list': [],
            'page_obj': None,
            'system': system.title(),
            'resource_type': resource_type,
            'page': page_number,
            'log_properties': []
        }

    return context

# 룰셋에 따른 로그 리스트를 보여주는 함수
def logs_by_ruleset(request, resourceType, system, ruleset_name):
    if system == 'fortinet':
        system = 'fortigate'
    elif system == 'genians':
        system = 'genian'
    try:
        page_number = int(request.GET.get('page', 1))
        res = es.search(index=f"{system}_ruleset", body={"query": {"match": {"name": ruleset_name}}})
        if res['hits']['total']['value'] == 0:
            return render(request, 'testing/finevo/error_page.html', {'error': f"No ruleset found with name {ruleset_name}"})
        
        # LogMangement 클래스 생성 후 rule query 지정
        system_log = LogManagement(system=system, page=page_number)
        rule = res['hits']['hits'][0]['_source']
        rule_query = rule["query"]["query"]
        system_log.query = rule_query

        # 필요한 값 받아서 보내주기
        total_count, log_list = system_log.search_logs()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Apply pagination
            page_obj = system_log.paginate()
            context = {
                'total_count': total_count,
                'log_list': log_list,
                'page_obj': page_obj,
                'page': page_obj['number'],
                'system': system.title(),
                'resource_type': resourceType,
                'log_properties': system_log.fetch_log_properties(), # 로그 프로퍼티 추출
                'table_properties': system_log.get_property_key()
            }
            return render(request, 'M_logs/elasticsearch/logs_by_ruleset.html', context=context)
        page_obj = system_log.paginate()
        context = {
            'total_count': total_count,
            'system': system.title(),
            'page_obj': page_obj,
            'log_list': log_list,
            'resource_type': resourceType,
            'ruleset_name': ruleset_name,
            'ruleset': json.dumps(rule, indent=4),  # 룰셋 세부 정보를 prettified JSON으로 추가
            'page': page_number,
            'log_properties': system_log.fetch_log_properties(), # 로그 프로퍼티 추출
            'table_properties': system_log.get_property_key()
        }
        return render(request, 'M_logs/elasticsearch/logs_by_ruleset.html', context=context)

    except ConnectionError as e:
        return JsonResponse({"error": f"Connection error: {e}"}, status=500)
    except Exception as e:
        return JsonResponse({"error": f"An error occurred: {e}"}, status=500)

def log_property_setting(request, resource_type, system):
    system=system.split('_')[0]
    if system == 'fortinet':
        system = 'fortigate'
    elif system == 'genians':
        system = 'genian'
    system_log = LogManagement(system=system, page=1)
    return system_log.save_table_property(request=request)