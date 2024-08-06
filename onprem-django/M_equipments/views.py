from django.views import View
from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from .src.resource.fortinet import fortinet_insert
from .src.resource.linux import linux_insert
from .src.resource.windows import windows_insert
from .src.resource.genians import genians_insert
from .src.resource.transmission import transmission_insert
from .src.resource.mssql import mssql_insert
from .src.resource.mysql import mysql_insert


from elasticsearch import Elasticsearch

ELASTICSEARCH_URL = "http://3.35.81.217:9200"


@method_decorator(login_required, name="dispatch")
class IntegrationView(View):
    def get(self, request, system=None, log_type=None):
        if system and log_type:
            return render(request, f"M_equipment/registration/{system}.html")
        else:
            context = {
                'integration_list': self.get_integration_list()
            }
            return render(request, f"M_equipment/integration.html", context)

    def post(self, request, system=None, log_type=None, action_type=None):
        if action_type == "check":
            pass
        elif action_type == "insert":
            context = globals()[f"{system.lower()}_insert"](request=request)
            if type(context) != str:
                return context
            else:
                return HttpResponse(context)

    def get_integration_list(self):
        try:
            es = Elasticsearch(ELASTICSEARCH_URL)
            query = {"query": {"match_all": {}}, "size": 1000, "from": 0}
            result = es.search(index='integration_info', body=query)
            integration_list = [integration['_source'] for integration in result['hits']['hits']]
            print(integration_list)
            return integration_list
        except Exception as e:
            print(e)
            return []
