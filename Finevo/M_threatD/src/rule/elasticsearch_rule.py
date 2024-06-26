import json
import requests
from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from elasticsearch import Elasticsearch, ConnectionError, NotFoundError
from deep_translator import GoogleTranslator

# Elasticsearch 클라이언트를 설정합니다.
es = Elasticsearch(hosts=["http://3.35.81.217:9200/"])


class RuleSet:
    def __init__(self, system):
        self.system = system
    
    def add_property(self, request):
        prop_type = request.POST.get('prop_type', '')
        return render(request, f"M_threatD/rules/elasticsearch/add/property_slot.html", context={"prop_type": prop_type})
    
    def add_ruleset(self, request):
        try:
            # 입력 데이터 로깅
            # logger.info(f"Request POST data: {request.POST}") 
            for key, val in request.POST.items():
                if val == '' or val is None:
                    return HttpResponse(f"Please Insert [ {' '.join(key.split('_')).title()} ] Correctly.")
            rule_name = request.POST.get('name')
            severity = int(request.POST.get('severity', 1))
            must_property_name = request.POST.getlist('must_property_name')
            must_property_value = request.POST.getlist('must_property_value')
            must_property_operator = request.POST.getlist('must_property_operator')
            not_property_name = request.POST.getlist('not_property_key')
            not_property_value = request.POST.getlist('not_property_val')
            not_property_operator = request.POST.getlist('not_property_operator')
            system = self.system
            
            print(not_property_operator)
            # logger.info(f"Parsed data: name={rule_name}, severity={severity}, must_property_name={must_property_name}, "
            #             f"must_property_value={must_property_value}, must_property_operator={must_property_operator}, "
            #             f"not_property_name={not_property_name}, not_property_value={not_property_value}, "
            #             f"not_property_operator={not_property_operator}, system={system}")

            # Elasticsearch 인덱스 설정
            index_mapping = {
                "linux": "linux_ruleset",
                "windows": "window_ruleset",
                "genians": "genian_ruleset",
                "fortinet": "fortigate_ruleset"
            }
            print(system)
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
            
            print(query)
            return HttpResponse(json.dumps(query, indent=4))

            # Logging 룰셋 정보
            # logger.info(f"Adding ruleset: {json.dumps(ruleset, indent=4)}")
            
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
                # logger.info(f"Successfully added ruleset: {json.dumps(output, indent=4)}")
                return JsonResponse(json.dumps(output, indent=4), status=201, content_type='application/json')
            else:
                # logger.error(f"Failed to add ruleset. Status code: {response.status_code}, Response: {response.text}")
                return HttpResponse(f"Status code: {response.status_code}\nFailed to add ruleset.")

        except Exception as e:
            print(e)
            # logger.error(f"Exception occurred: {e}", exc_info=True)
            return HttpResponse("Failed to add ruleset. Please try again.")
        
    
def rule_config_page(request, system):
    return render(request, 'M_threatD/rules/elasticsearch/rule.html', context={'system': system})

def rule_config_action(request, resourceType, system, action_type):
    if request.method == 'POST':
        try:
            system = system.split('_')[0]
            rule_set = RuleSet(system=system)
            return HttpResponse(getattr(rule_set, action_type)(request=request))
        except Exception as e:
            print(e)
            return HttpResponse('Wrong Request. Please Try Again.')
    else:
        return HttpResponse('Wrong Reqeust. Please Try Again.')