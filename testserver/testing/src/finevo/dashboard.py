# local
import json
import requests
from collections import defaultdict, Counter
from django.shortcuts import render, HttpResponse, redirect
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseBadRequest
from datetime import datetime, timedelta, timezone
import time

from elasticsearch import Elasticsearch


es = Elasticsearch("http://3.35.81.217:9200/")

def dashboard(request):
    context = {'test': session_overtime()}
    print(session_overtime())
    
    return render(request, 'testing/finevo/dashboard.html', context)


def session_overtime():
    query = {
            "query": {
                "match_all": {}
            },
            "size": 300
        }
    result = es.search(index='test_genian_syslog', body=query)
    session_overtime = defaultdict(int)
    traffic_overtime = defaultdict(lambda: {'sent': 0, 'received': 0})
    for hit in result['hits']['hits']:
        log = hit['_source']
        timestamp = datetime.strptime(log.get('@timestamp'), "%Y-%m-%dT%H:%M:%S.%f")
        time_key = timestamp.strftime('%Y-%m-%d %H:%M')

        session_overtime[time_key] += 1

        sent_byte = int(log.get('sentbyte', 0))
        rcvd_byte = int(log.get('rcvdbyte', 0))
        traffic_overtime[time_key]['sent'] += sent_byte
        traffic_overtime[time_key]['received'] += rcvd_byte
        
    return session_overtime, traffic_overtime
    
    