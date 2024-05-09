# local
import json
import requests

from django.shortcuts import render, HttpResponse, redirect
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseBadRequest

from elasticsearch import Elasticsearch

class LogManagement():
    def __init__(self, system:str):
        self.es = Elasticsearch("http://3.35.81.217:9200/")
        # self.es = Elasticsearch("http://44.204.132.232:9200/")
        self.system = system
        self.query = {"match_all":{}}
        # self.query = {"exists":{"field": "detected_rules"}}
    
    def paginator(self):
        pass
    
    def search_logs(self):
        try:
            # response = self.es.search(index=f"test_{self.system}_syslog", scroll='1m', query=self.query, size=1000, sort=[{"@timestamp":{'order': 'desc'}}])
            response = self.es.search(index=f"test_{self.system}_syslog", scroll='1m', query=self.query, size=100)
            log_list = [hit['_source'] for hit in response['hits']['hits']]
            total_count = response['hits']['total']['value']
        except:
            total_count = 0
            log_list = []
        # print(log_list)
        context = {
            'total_count': total_count,
            'log_list': log_list,
            'system': self.system.title(),
            'query': self.query,
            'page': 1
        }
        return context
        
    def filter_query(self, query):
        page = query.pop('page') if 'page' in query else 'no page'
        print(page)
        for clause in query:
            try:
                new_clause = json.loads(query[clause].replace("'", '"'))
            except:
                new_clause = []
            finally:
                query[clause] = new_clause
        # query['must'].append({"exists": {"field": "detected_rules"}})
        if 'should' in query and len(query['should']) != 0 : query.update({"minimum_should_match": 1})
        self.query = {
            "bool": query
        }
        # print(self.query)
        return self.search_logs()
    
    def filter_properties(self):
        pass
    

def list_logs(request, system):
    system_log = LogManagement(system=system)
    if 'query' in request.GET and len(request.GET['query']) != 0:
        query = eval(request.GET.dict()['query'].strip('"'))
        for key, val in query.items():
            if len(val) == 0:
                query[key] = ''
            else:
                query[key] = json.dumps(val)
            
        context = system_log.filter_query(query)
    elif not any(key in request.GET for key in ['should', 'must', 'must_not']):
        context = system_log.search_logs()
    else:
        context = system_log.filter_query(request.GET.dict())
    
    return render(request, 'testing/finevo/elasticsearch.html', context= context)  
