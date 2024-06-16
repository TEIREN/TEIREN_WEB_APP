import json
from django.shortcuts import render, HttpResponse
from django.http import JsonResponse
from elasticsearch import Elasticsearch, ConnectionError, NotFoundError

# Elasticsearch 클라이언트를 설정합니다.
es = Elasticsearch(hosts=["http://3.35.81.217:9200/"])
    
def save_table_property(request, system):
    document = {'system': system, 'properties': [property for property in dict(request.GET)['properties'] if property]}
    print(request.GET.get('properties'))
    try:
        es.update_by_query(index="table_property", body={
            "query":{
                "match": {"system": system}
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

def get_property_key(system):
    try:
        response = es.search(index=f"table_property", body={"query": {"match": {'system': system}}})
        return response['hits']['hits'][0]['_source']['properties']
    except Exception as e:
        print(e)
        return []
