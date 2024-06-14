import json
from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from elasticsearch import Elasticsearch, ConnectionError

# Elasticsearch 클라이언트를 설정합니다.
es = Elasticsearch(hosts=["http://3.35.81.217:9200/"])
    
def save_table_property(request, system):
    print(request.GET.dict())
    print(system)
    # try:
    #     es.index(index=f"table_property", document=request)
    # except ConnectionError as e:
    #     return JsonResponse({"error": f"Connection error: {e}"}, status=500)
    # except Exception as e:
    #     return JsonResponse({"error": f"An error occurred: {e}"}, status=500)
    return HttpResponse('xxx')

def get_property_key(system):
    try:
        res = es.search(index=f"table_property", body={"query": {"match": {'system': system}}})
        return ['test', 'testx']
    except:
        return []
