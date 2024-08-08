import json
import logging
import requests
from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from elasticsearch import Elasticsearch

# URL 하드 코딩된거 수정해야함 
# mysql mssql 설정을 추가
# 또한 flunetd는 태그 네임 기준으로 룰셋 이름이 들어가도록 설계
# Elasticsearch 클라이언트를 설정합니다.
es = Elasticsearch(hosts=["http://3.35.81.217:9200/"])  # 올바른 Elasticsearch 서버 IP 주소로 변경

class RuleSet:
    def __init__(self, system):
        self.system = system

    def get_ruleset_list(self, rule_type: str):
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
                rule['severity'] = [color_list[num - 1], severity_list[num - 1]]
        except Exception as e:
            logging.error(f"Error retrieving ruleset list: {e}")
            response = []
        finally:
            return response
    
    def get_detail_page(self, request):
        context = request.POST.dict()
        context['severity'] = json.loads(context['severity'].replace("'", '"'))
        context['query'] = json.dumps(json.loads(context['query'].replace("'", '"')), indent=4)
        return render(request, f"M_threatD/rules/elasticsearch/custom/details.html", context=context)
    
    def add_property(self, request):
        return render(request, f"M_threatD/rules/elasticsearch/add/property_slot.html")

    def add_ruleset(self, request):
        try:
            rule_name = request.POST.get('name', '').strip()
            severity = int(request.POST.get('severity', 1))
            must_property_name = request.POST.getlist('must_property_name')
            must_property_value = request.POST.getlist('must_property_value')
            must_property_operator = request.POST.getlist('must_property_operator')

            if not rule_name:
                return HttpResponse("Rule name cannot be empty.", status=400)

            # index_mapping = {
            #     "linux": "linux_ruleset",
            #     "window": "window_ruleset",
            #     "genian": "genian_ruleset",
            #     "fortigate": "fortigate_ruleset"
            # }
            
            index_name = f"{self.system}_ruleset"

            # index_name = index_mapping.get(system)
            if not index_name:
                return HttpResponse("Invalid system choice.", status=400)

            must_conditions = []

            property_conditions = {}
            for m_name, m_value, m_operator in zip(must_property_name, must_property_value, must_property_operator):
                m_name = m_name.strip().lower()
                m_value = m_value.strip().lower()

                condition = None
                if m_operator == '=':
                    condition = {"match": {m_name: m_value}}
                elif m_operator == '!=':
                    condition = {"bool": {"must_not": {"match": {m_name: m_value}}}}

                if m_name not in property_conditions:
                    property_conditions[m_name] = []

                property_conditions[m_name].append(condition)

            for prop, conditions in property_conditions.items():
                must_conditions.append({"bool": {"should": conditions, "minimum_should_match": 1}})

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
                "system": self.system,
                "query": query,
                "severity": severity,
                "status": 1,  # 기본값 추가
                "seen": 0,    # 기본값 추가
                "rule_type": "custom"
            }

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

            url = f"http://3.35.81.217:9200/{index_name}/_doc"
            headers = {
                "Content-Type": "application/json"
            }

            response = requests.post(url, headers=headers, json=ruleset)

            if response.status_code == 201:
                return HttpResponse(f"Successfully added ruleset: {rule_name}")
            else:
                logging.error(f"Failed to add ruleset. Status code: {response.status_code}, Response: {response.text}")
                return HttpResponse(f"Failed to add ruleset. Status code: {response.status_code}", status=400)

        except Exception as e:
            logging.error(f"Exception occurred: {e}", exc_info=True)
            return HttpResponse("Failed to add ruleset. Please try again.", status=500)

    def status_off(self, request):
        try:
            rule_name = request.POST.get('name', '').strip()
            if not rule_name:
                return HttpResponse("Rule name cannot be empty.", status=400)

            index_mapping = {
                "linux": "linux_ruleset",
                "window": "window_ruleset",
                "genian": "genian_ruleset",
                "fortigate": "fortigate_ruleset"
            }

            index_name = index_mapping.get(self.system)
            if not index_name:
                return HttpResponse("Invalid system choice.", status=400)

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
                    rule_status = hit["_source"].get("status", 1)
                    if rule_status == 0:
                        return HttpResponse(f"Rule '{rule_name}' is already inactive.", status=400)

                    update_url = f"http://3.35.81.217:9200/{index_name}/_update/{doc_id}"
                    update_response = requests.post(update_url, headers={"Content-Type": "application/json"}, json={"doc": {"status": 0}})

                    if update_response.status_code == 200:
                        return HttpResponse(f"Successfully deactivated rule: {rule_name}", status=200)
                    else:
                        logging.error(f"Failed to update rule status. Status code: {update_response.status_code}, Response: {update_response.text}")
                        return HttpResponse(f"Failed to update rule status. Status code: {update_response.status_code}", status=400)

            else:
                logging.error(f"Failed to search for rule. Status code: {search_response.status_code}, Response: {search_response.text}")
                return HttpResponse(f"Failed to search for rule. Status code: {search_response.status_code}", status=400)

        except Exception as e:
            logging.error(f"Exception occurred: {e}", exc_info=True)
            return HttpResponse("Failed to deactivate rule. Please try again.", status=500)

    def status_on(self, request):
        try:
            rule_name = request.POST.get('name', '').strip()
            if not rule_name:
                return HttpResponse("Rule name cannot be empty.", status=400)

            index_mapping = {
                "linux": "linux_ruleset",
                "window": "window_ruleset",
                "genian": "genian_ruleset",
                "fortigate": "fortigate_ruleset"
            }

            index_name = index_mapping.get(self.system)
            if not index_name:
                return HttpResponse("Invalid system choice.", status=400)

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
                    rule_status = hit["_source"].get("status", 0)
                    if rule_status == 1:
                        return HttpResponse(f"Rule '{rule_name}' is already active.", status=400)

                    update_url = f"http://3.35.81.217:9200/{index_name}/_update/{doc_id}"
                    update_response = requests.post(update_url, headers={"Content-Type": "application/json"}, json={"doc": {"status": 1}})

                    if update_response.status_code == 200:
                        return HttpResponse(f"Successfully activated rule: {rule_name}", status=200)
                    else:
                        logging.error(f"Failed to update rule status. Status code: {update_response.status_code}, Response: {update_response.text}")
                        return HttpResponse(f"Failed to update rule status. Status code: {update_response.status_code}", status=400)

            else:
                logging.error(f"Failed to search for rule. Status code: {search_response.status_code}, Response: {search_response.text}")
                return HttpResponse(f"Failed to search for rule. Status code: {search_response.status_code}", status=400)

        except Exception as e:
            logging.error(f"Exception occurred: {e}", exc_info=True)
            return HttpResponse("Failed to activate rule. Please try again.", status=500)
