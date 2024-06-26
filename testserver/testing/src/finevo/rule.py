import json
import logging
import requests
from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from elasticsearch import Elasticsearch

# Elasticsearch 클라이언트를 설정합니다.
es = Elasticsearch(hosts=["http://3.35.81.217:9200/"])  # 올바른 Elasticsearch 서버 IP 주소로 변경

# Logging 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RuleSet:
    def __init__(self, system):
        self.system = system

    def add_property(self, request):
        prop_type = request.POST.get('prop_type', '')
        return render(request, f"testing/finevo/rules/add/property_slot.html", context={"prop_type": prop_type})

    def add_ruleset(self, request):
        try:
            # 입력 데이터 로깅
            logger.info(f"Request POST data: {request.POST}")

            rule_name = request.POST.get('name')
            severity = int(request.POST.get('severity', 1))
            must_property_name = request.POST.getlist('must_property_name')
            must_property_value = request.POST.getlist('must_property_value')
            must_property_operator = request.POST.getlist('must_property_operator')
            not_property_name = request.POST.getlist('not_property_key')
            not_property_value = request.POST.getlist('not_property_val')
            not_property_operator = request.POST.getlist('not_property_operator')
            system = self.system

            logger.info(f"Parsed data: name={rule_name}, severity={severity}, must_property_name={must_property_name}, "
                        f"must_property_value={must_property_value}, must_property_operator={must_property_operator}, "
                        f"not_property_name={not_property_name}, not_property_value={not_property_value}, "
                        f"not_property_operator={not_property_operator}, system={system}")

            # Elasticsearch 인덱스 설정
            index_mapping = {
                "linux": "linux_ruleset",
                "windows": "window_ruleset",
                "genian": "genian_ruleset",
                "fortigate": "fortigate_ruleset"
            }

            index_name = index_mapping.get(system)
            if not index_name:
                return HttpResponse("Invalid system choice.", status=400)

            must_clauses = []
            not_clauses = []

            for m_name, m_value, m_operator in zip(must_property_name, must_property_value, must_property_operator):
                if m_operator == '=':
                    must_clauses.append({"match": {m_name.strip(): m_value.strip()}})
                else:
                    must_clauses.append({"bool": {"must_not": {"match": {m_name.strip(): m_value.strip()}}}})

            for n_name, n_value, n_operator in zip(not_property_name, not_property_value, not_property_operator):
                if n_name.strip() and n_value.strip():  # Ensure the name and value are not empty
                    if n_operator == '=':
                        not_clauses.append({"match": {n_name.strip(): n_value.strip()}})
                    else:
                        not_clauses.append({"bool": {"must_not": {"match": {n_name.strip(): n_value.strip()}}}})

            # must 및 must_not 조건이 비어 있을 수 있도록 처리
            bool_query = {}
            if must_clauses:
                bool_query['must'] = must_clauses
            if not_clauses:
                bool_query['must_not'] = not_clauses

            query = {
                "query": {
                    "bool": bool_query
                }
            }

            ruleset = {
                "name": rule_name.strip(),  # Ensure the name field is assigned correctly and stripped of whitespace
                "system": system,
                "query": query,
                "severity": severity,
                "rule_type": "custom"  # Add the rule_type property
            }

            # 이름 중복 확인
            name_search_query = {
                "query": {
                    "term": {
                        "name": rule_name.strip()
                    }
                }
            }

            name_search_url = f"http://3.35.81.217:9200/{index_name}/_search"
            name_search_response = requests.get(name_search_url, headers={"Content-Type": "application/json"}, json=name_search_query)

            if name_search_response.status_code == 200:
                name_hits = name_search_response.json()['hits']['hits']
                if name_hits:
                    return HttpResponse(f"Rule with name '{rule_name}' already exists.", status=400)

            # 쿼리 중복 확인
            query_search_query = {
                "query": {
                    "match_all": {}
                }
            }

            query_search_url = f"http://3.35.81.217:9200/{index_name}/_search"
            query_search_response = requests.get(query_search_url, headers={"Content-Type": "application/json"}, json=query_search_query)

            if query_search_response.status_code == 200:
                query_hits = query_search_response.json()['hits']['hits']
                for hit in query_hits:
                    if json.dumps(hit['_source']['query'], sort_keys=True) == json.dumps(query, sort_keys=True):
                        return HttpResponse("A rule with the same query already exists.", status=400)

            # Logging 룰셋 정보
            logger.info(f"Adding ruleset: {json.dumps(ruleset, indent=4)}")

            # Elasticsearch에 룰셋 추가
            url = f"http://3.35.81.217:9200/{index_name}/_doc"
            headers = {
                "Content-Type": "application/json"
            }

            response = requests.post(url, headers=headers, json=ruleset)

            if response.status_code == 201:
                output = {
                    "name": rule_name.strip(),  # Ensure the name field is returned correctly and stripped of whitespace
                    "severity": severity,
                    "must_property_name": must_property_name,
                    "must_property_value": must_property_value,
                    "must_property_operator": must_property_operator,
                    "not_property_name": not_property_name,
                    "not_property_value": not_property_value,
                    "not_property_operator": not_property_operator,
                    "system": system,
                    "rule_type": "custom"  # Add the rule_type property to the output
                }
                logger.info(f"Successfully added ruleset: {json.dumps(output, indent=4)}")
                return JsonResponse(output, status=201)
            else:
                logger.error(f"Failed to add ruleset. Status code: {response.status_code}, Response: {response.text}")
                return HttpResponse(f"Failed to add ruleset. Status code: {response.status_code}", status=400)

        except Exception as e:
            logger.error(f"Exception occurred: {e}", exc_info=True)
            return HttpResponse("Failed to add ruleset. Please try again.", status=500)

def rule_config_page(request, system):
    return render(request, 'testing/finevo/rules/rule.html', context={'system': system})

def rule_config_action(request, system, action_type):
    if request.method == 'POST':
        try:
            rule_set = RuleSet(system=system)
            return HttpResponse(getattr(rule_set, action_type)(request=request))
        except Exception as e:
            logger.error(f"Exception occurred: {e}", exc_info=True)
            return HttpResponse('Wrong Request. Please Try Again.', status=400)
    else:
        return HttpResponse('Wrong Request. Please Try Again.', status=400)
