import json
from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from elasticsearch import Elasticsearch, ConnectionError, NotFoundError

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
            request_dict = dict(request.POST)
            name = request.POST.get('name', '')
            severity = request.POST.get('severity', 1)
            must_property_name = request_dict.get('must_property_name', [])
            must_property_value = request_dict.get('must_property_value', [])
            must_property_operator = request_dict.get('must_property_operator', [])
            not_property_name = request_dict.get('not_property_name', [])
            not_property_value = request_dict.get('not_property_value', [])
            not_property_operator = request_dict.get('not_property_operator', [])
            system = self.system
            return "Successfully added ruleset"
        except Exception as e:
            print(e)
            return "Failed to add ruleset. Please try again."
        
    
def rule_config_page(request, system):
    return render(request, 'M_threatD/rules/elasticsearch/rule.html', context={'system': system})

def rule_config_action(request, resourceType, system, action_type):
    if request.method == 'POST':
        try:
            rule_set = RuleSet(system=system)
            return HttpResponse(getattr(rule_set, action_type)(request=request))
        except Exception as e:
            print(e)
            return HttpResponse('Wrong Request. Please Try Again.')
    else:
        return HttpResponse('Wrong Reqeust. Please Try Again.')