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

    def get_ruleset_list(self, rule_type:str):
        try:
            es.indices.put_settings(index=f"{self.system}_ruleset", body={"index.max_result_window": 1000000})
            _search = es.search(index=f"{self.system}_ruleset", body={
                "query": {
                    "match": {
                        "rule_type": f"{rule_type}"
                    }
                }
            })
            hits = _search['hits']['hits']
            response = [hit['_source'] for hit in hits]
            color_list = ['success', 'warning', 'caution', 'danger']
            severity_list = ['LOW', 'MID', 'HIGH', 'CRITICAL']
            for rule in response:
                num = int(rule['severity'])
                rule['severity'] = [color_list[num-1], severity_list[num-1]]
        except Exception as e:
            print(e)
            response = []
        finally:
            return response
    def get_detail_page(self, request):
        context = request.POST.dict()
        print(context['query'])
        print(type(context['query']))
        context['query'] = json.dumps(json.loads(context['query'].replace("'", '"')), indent=4)
        return render(request, f"testing/finevo/rules/custom/details.html", context=context)
    
    def add_property(self, request):
        return render(request, f"testing/finevo/rules/add/property_slot.html")

    def add_ruleset(self, request):
        try:
            # 입력 데이터 로깅
            logger.info(f"Request POST data: {request.POST}")

            rule_name = request.POST.get('name', '').strip()
            severity = int(request.POST.get('severity', 1))
            must_property_name = request.POST.getlist('must_property_name')
            must_property_value = request.POST.getlist('must_property_value')
            must_property_operator = request.POST.getlist('must_property_operator')
            system = self.system

            if not rule_name:
                return HttpResponse("Rule name cannot be empty.", status=400)

            logger.info(f"Parsed data: name={rule_name}, severity={severity}, must_property_name={must_property_name}, "
                        f"must_property_value={must_property_value}, must_property_operator={must_property_operator}, system={system}")

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

            must_conditions = []
            should_conditions = {}

            # must 조건 생성
            for m_name, m_value, m_operator in zip(must_property_name, must_property_value, must_property_operator):
                if m_operator == '=':
                    if m_name not in should_conditions:
                        should_conditions[m_name] = []
                    should_conditions[m_name].append({"match": {m_name.strip().lower(): m_value.strip().lower()}})
                elif m_operator == '!=':
                    must_conditions.append({"bool": {"must_not": {"match": {m_name.strip().lower(): m_value.strip().lower()}}}})

            # should_conditions를 must_conditions로 변환
            for key, conditions in should_conditions.items():
                must_conditions.append({"bool": {"should": conditions, "minimum_should_match": 1}})

            # must 조건이 비어 있을 수 있도록 처리
            bool_query = {}
            if must_conditions:
                bool_query['must'] = must_conditions

            query = {
                "query": {
                    "bool": bool_query
                }
            }

            ruleset = {
                "name": rule_name,
                "system": system,
                "query": query,
                "severity": severity,
                "rule_type": "custom"  # Add the rule_type property
            }

            # 이름 중복 확인
            name_search_query = {
                "query": {
                    "term": {
                        "name": rule_name
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
            logger.info(f"Adding ruleset: {json.dumps(ruleset, indent=4, ensure_ascii=False)}")

            # Elasticsearch에 룰셋 추가
            url = f"http://3.35.81.217:9200/{index_name}/_doc"
            headers = {
                "Content-Type": "application/json"
            }

            response = requests.post(url, headers=headers, json=ruleset)

            if response.status_code == 201:
                output = {
                    "name": rule_name,
                    "severity": severity,
                    "must_property_name": must_property_name,
                    "must_property_value": must_property_value,
                    "must_property_operator": must_property_operator,
                    "system": system,
                    "rule_type": "custom"  # Add the rule_type property to the output
                }
                logger.info(f"Successfully added ruleset: {json.dumps(output, indent=4, ensure_ascii=False)}")
                return JsonResponse(output, status=201)
            else:
                logger.error(f"Failed to add ruleset. Status code: {response.status_code}, Response: {response.text}")
                return HttpResponse(f"Failed to add ruleset. Status code: {response.status_code}", status=400)

        except Exception as e:
            logger.error(f"Exception occurred: {e}", exc_info=True)
            return HttpResponse("Failed to add ruleset. Please try again.", status=500)
        
    def remove_rule(self, request):
        try:
            rule_name = request.POST.get('name', '').strip()

            if not rule_name:
                return HttpResponse("Rule name cannot be empty.", status=400)

            logger.info(f"Removing rule with name: {rule_name}")

            # Elasticsearch 인덱스 설정
            index_mapping = {
                "linux": "linux_ruleset",
                "windows": "window_ruleset",
                "genian": "genian_ruleset",
                "fortigate": "fortigate_ruleset"
            }

            # 모든 시스템의 인덱스에서 룰셋을 삭제
            for system, index_name in index_mapping.items():
                delete_query = {
                    "query": {
                        "bool": {
                            "must": [
                                {"match": {"name": rule_name}}
                            ]
                        }
                    }
                }

                delete_url = f"http://3.35.81.217:9200/{index_name}/_delete_by_query"
                delete_response = requests.post(delete_url, headers={"Content-Type": "application/json"}, json=delete_query)

                if delete_response.status_code == 200:
                    logger.info(f"Successfully removed rule: {rule_name} from {system} ruleset")
                else:
                    logger.error(f"Failed to remove rule from {system} ruleset. Status code: {delete_response.status_code}, Response: {delete_response.text}")

            return HttpResponse(f"Successfully removed rule: {rule_name}", status=200)

        except Exception as e:
            logger.error(f"Exception occurred: {e}", exc_info=True)
            return HttpResponse("Failed to remove rule. Please try again.", status=500)

    def update_ruleset(self, request):
        try:
            rule_name = request.POST.get('name', '').strip()
            severity = int(request.POST.get('severity', 1))
            must_property_name = request.POST.getlist('must_property_name')
            must_property_value = request.POST.getlist('must_property_value')
            must_property_operator = request.POST.getlist('must_property_operator')
            system = self.system

            if not rule_name:
                return HttpResponse("Rule name cannot be empty.", status=400)

            logger.info(f"Parsed data for update: name={rule_name}, severity={severity}, must_property_name={must_property_name}, "
                        f"must_property_value={must_property_value}, must_property_operator={must_property_operator}, system={system}")

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

            must_conditions = []
            should_conditions = {}

            # must 조건 생성
            for m_name, m_value, m_operator in zip(must_property_name, must_property_value, must_property_operator):
                if m_operator == '=':
                    if m_name not in should_conditions:
                        should_conditions[m_name] = []
                    should_conditions[m_name].append({"match": {m_name.strip().lower(): m_value.strip().lower()}})
                elif m_operator == '!=':
                    must_conditions.append({"bool": {"must_not": {"match": {m_name.strip().lower(): m_value.strip().lower()}}}})

            # should_conditions를 must_conditions로 변환
            for key, conditions in should_conditions.items():
                must_conditions.append({"bool": {"should": conditions, "minimum_should_match": 1}})

            # must 조건이 비어 있을 수 있도록 처리
            bool_query = {}
            if must_conditions:
                bool_query['must'] = must_conditions

            query = {
                "query": {
                    "bool": bool_query
                }
            }

            updated_ruleset = {
                "name": rule_name,
                "system": system,
                "query": query,
                "severity": severity,
                "rule_type": "custom"  # Add the rule_type property
            }

            # 기존 룰셋 업데이트
            search_query = {
                "query": {
                    "term": {
                        "name": rule_name
                    }
                }
            }

            search_url = f"http://3.35.81.217:9200/{index_name}/_search"
            search_response = requests.get(search_url, headers={"Content-Type": "application/json"}, json=search_query)

            if search_response.status_code == 200:
                search_hits = search_response.json()['hits']['hits']
                if not search_hits:
                    return HttpResponse(f"Rule with name '{rule_name}' does not exist.", status=404)

                for hit in search_hits:
                    doc_id = hit["_id"]
                    update_url = f"http://3.35.81.217:9200/{index_name}/_update/{doc_id}"
                    update_response = requests.post(update_url, headers={"Content-Type": "application/json"}, json={"doc": updated_ruleset})

                    if update_response.status_code == 200:
                        logger.info(f"Successfully updated rule: {rule_name} in {index_name}")
                    else:
                        logger.error(f"Failed to update rule. Status code: {update_response.status_code}, Response: {update_response.text}")
                        return HttpResponse(f"Failed to update rule. Status code: {update_response.status_code}", status=400)

                return HttpResponse(f"Successfully updated rule: {rule_name}", status=200)
            else:
                logger.error(f"Failed to search for rule to update. Status code: {search_response.status_code}, Response: {search_response.text}")
                return HttpResponse(f"Failed to search for rule to update. Status code: {search_response.status_code}", status=400)

        except Exception as e:
            logger.error(f"Exception occurred: {e}", exc_info=True)
            return HttpResponse("Failed to update ruleset. Please try again.", status=500)

def rule_config_page(request, system):
    ruleset = RuleSet(system=system)
    context = {
        'system': system,
        'custom_ruleset': ruleset.get_ruleset_list(rule_type='custom'),
        'default_ruleset': ruleset.get_ruleset_list(rule_type='default')
    }
    return render(request, 'testing/finevo/rules/rule.html', context=context)

def rule_config_action(request, system, action_type):
    if request.method == 'POST':
        try:
            ruleset = RuleSet(system=system)
            return HttpResponse(getattr(ruleset, action_type)(request=request))
        except Exception as e:
            logger.error(f"Exception occurred: {e}", exc_info=True)
            return HttpResponse('Wrong Request. Please Try Again.', status=400)
    else:
        return HttpResponse('Wrong Request. Please Try Again.', status=400)