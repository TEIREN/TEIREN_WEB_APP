from django.shortcuts import render, redirect, HttpResponse
from django.http import JsonResponse
from py2neo import Graph
from django.conf import settings
import json

# AWS
host = settings.NEO4J['HOST']
port = settings.NEO4J["PORT"]
username = settings.NEO4J['USERNAME']
password = settings.NEO4J['PASSWORD']
graph = Graph(f"bolt://{host}:{port}", auth=(username, password))


## Integration List
# def list_integration():
#     global collection
#     result = collection.find()
#     if result:
#         data = {}
#         for num, doc in enumerate (list(result), start=1):
#             doc.pop('_id')
#             data[num] = doc
#         data = {'list': data}
#         return data
#     return {'test': 0}
def list_integration():
    cypher = f"""
    MATCH (i:Integration)
    WITH i.integrationType as type, {{ACCESS_KEY: i.accessKey, SECRET_KEY: i.secretKey}} as keys
    WITH apoc.map.fromLists([type], [keys]) as Integration
    RETURN Integration
    """
    results = graph.run(cypher)
    data = {}
    for num, result in enumerate (results, start=1):
            data[num] = result['Integration']
    return {'list': data}

## Integration delete
def delete_integration(request):
    cloud = request['cloud']
    main = request['main']
    sub = request['sub']
    cypher = f"""
    MATCH (i:Integration {{integrationType:'{cloud}', accessKey:'{main}', secretKey:'{sub}'}})
    DETACH DELETE i
    RETURN COUNT(i)
    """
    if  graph.evaluate(cypher) > 0:
        return '로그 수집 중단 완료'
    else:
        return '로그 수집 중단 실패'

# ## NCP Cloud Activity Tracer
# def integration_NCP(request):
#     from .api_ncp import CloudActivityTracer
#     if request.method == 'POST':
#         data = {}
#         access_key = request.POST['access_key'].encode('utf-8').decode('iso-8859-1')  # 한글 입력 시 에러 발생 방지
#         if access_key == '':
#             data['class'] = 'btn btn-danger'
#             data['value'] = 'ACCESS KEY를 입력해주세요'
#             return JsonResponse(data)
#         secret_key = request.POST['secret_key'].encode('utf-8').decode('iso-8859-1')  # 한글 입력 시 에러 발생 방지
#         if secret_key == '':
#             data['class'] = 'btn btn-danger'
#             data['value'] = 'SECRET KEY를 입력해주세요'
#             return JsonResponse(data)
#         folder_name = request.POST['folder_name'].encode('utf-8').decode('iso-8859-1')
#         bucket_name = request.POST['bucket_name'].encode('utf-8').decode('iso-8859-1')
#         doc = {
#             'NCP_API.ACCESS_KEY': access_key,
#             'NCP_API.SECRET_KEY': secret_key
#         }
#         global collection
#         result = collection.find_one(doc)
#         if result:
#             data['class'] = 'btn btn-warning'
#             data['value'] = '이미 등록된 정보입니다.'
#         else:
#             if CloudActivityTracer(access_key, secret_key):
#                 data['class'] = 'btn btn-success'
#                 data['value'] = ' ✓ 키 인증 및 Cloudtrail 서비스 사용 확인 완료!'
#                 data['modal'] = {}
#                 data['modal']['access_key'] = access_key
#                 data['modal']['secret_key'] = secret_key
#                 data['modal']['folder_name'] = folder_name
#                 data['modal']['bucket_name'] = bucket_name
#             else:
#                 data['class'] = 'btn btn-danger'
#                 data['value'] = '인증 실패 (재시도)'
#         return JsonResponse(data)
#     data = {}
#     data['class'] = 'btn btn-danger'
#     data['value'] = '인증 실패 (재시도)'
#     return JsonResponse(data)

# def insert_NCP(request):
#     if request.method == 'POST':
#         access_key = request.POST['modal_access_key'].encode('utf-8').decode('iso-8859-1')
#         secret_key = request.POST['modal_secret_key'].encode('utf-8').decode('iso-8859-1')
#         folder_name = request.POST['modal_folder_name'].encode('utf-8').decode('iso-8859-1')
#         bucket_name = request.POST['modal_bucket_name'].encode('utf-8').decode('iso-8859-1')
#         global collection
#         doc = {"NCP_API": {
#             "ACCESS_KEY": access_key,
#             "SECRET_KEY": secret_key,
#             "FOLDER_NAME": folder_name,
#             "BUCKET_NAME": bucket_name
#         }}
#         try:
#             collection.insert_one(doc)
#             data = "<span class='text-primary'>로그 수집/통합 설정 완료 </span>"
#         except:
#             data = "등록 실패"
#         finally:
#             return HttpResponse(data)

# ## NHN CLOUD
# def integration_NHN(request):
#     if request.method == 'POST':
#         data = {}
#         access_key = request.POST['access_key'].encode('utf-8').decode('iso-8859-1')
#         if access_key == '':
#             data['class'] = 'btn btn-danger'
#             data['value'] = 'NHN Cloud 회원 정보를 입력해주세요'
#             return JsonResponse(data)
#         secret_key = request.POST['secret_key'].encode('utf-8').decode('iso-8859-1')
#         if secret_key == '':
#             data['class'] = 'btn btn-danger'
#             data['value'] = 'APP KEY를 입력해주세요'
#             return JsonResponse(data)
#         doc = {
#             'NHN_API.ACCESS_KEY': access_key,
#             'NHN_API.SECRET_KEY': secret_key
#         }
#         global collection
#         result = collection.find_one(doc)
#         if result:
#             data['class'] = 'btn btn-warning'
#             data['value'] = '이미 등록된 정보입니다.'
#         else:
#             return False
#     return False

# def insert_NHN(request):
#     if request.method == 'POST':
#         access_key = request.POST['modal_access_key'].encode('utf-8').decode('iso-8859-1')
#         secret_key = request.POST['modal_secret_key'].encode('utf-8').decode('iso-8859-1')
#         global collection
#         doc = {"NHN_API": {
#             "ACCESS_KEY": access_key,
#             "SECRET_KEY": secret_key
#         }}
#         try:
#             collection.insert_one(doc)
#             data = "<span class='text-primary'>로그 수집/통합 설정 완료 </span>"
#         except:
#             data = "등록 실패"
#         finally:
#             return HttpResponse(data)
#     return False

## AWS CLOUD
def integration_AWS(request):
    import boto3
    if request.method == 'POST':
        data = {}
        access_key = request.POST['access_key'].encode('utf-8').decode('iso-8859-1')  # 한글 입력 시 에러 발생 방지
        if access_key == '':
            data['class'] = 'btn btn-danger'
            data['value'] = 'ACCESS KEY를 입력해주세요'
            return JsonResponse(data)
        secret_key = request.POST['secret_key'].encode('utf-8').decode('iso-8859-1')  # 한글 입력 시 에러 발생 방지
        if secret_key == '':
            data['class'] = 'btn btn-danger'
            data['value'] = 'SECRET KEY를 입력해주세요'
            return JsonResponse(data)
        region_name = request.POST['region_name'].encode('utf-8').decode('iso-8859-1')
        bucket_name = request.POST['bucket_name'].encode('utf-8').decode('iso-8859-1')
        cypher = f"""
        MATCH (i:Integration)
        WHERE i.integrationType = 'Aws'
            AND i.accessKey = '{access_key}'
            AND i.secretKey = '{secret_key}'
        RETURN count(i)
        """
        if graph.evaluate(cypher) > 0 :
            data['class'] = 'btn btn-warning'
            data['value'] = '이미 등록된 정보입니다.'
        else:
            session = boto3.Session(
                aws_access_key_id = access_key,
                aws_secret_access_key = secret_key
            )
            try:
                s3_client = session.client('s3')
                s3_client.list_buckets()
                data['class'] = 'btn btn-success'
                data['value'] = ' ✓ 키 인증 및 Cloudtrail 서비스 사용 확인 완료!'
                data['modal'] = {}
                data['modal']['access_key'] = access_key
                data['modal']['secret_key'] = secret_key
                data['modal']['reigion_name'] = region_name
                data['modal']['bucket_name'] = bucket_name
            except Exception:
                data['class'] = 'btn btn-danger'
                data['value'] = '인증 실패 (재시도)'
            finally:
                return JsonResponse(data)
        return JsonResponse(data)
    data = {}
    data['class'] = 'btn btn-danger'
    data['value'] = '인증 실패 (재시도)'
    return JsonResponse(data)

def insert_AWS(request):
    if request.method == 'POST':
        access_key = request.POST['modal_access_key'].encode('utf-8').decode('iso-8859-1')
        secret_key = request.POST['modal_secret_key'].encode('utf-8').decode('iso-8859-1')
        region_name = request.POST['modal_region_name'].encode('utf-8').decode('iso-8859-1')
        bucket_name = request.POST['modal_bucket_name'].encode('utf-8').decode('iso-8859-1')
        cypher = f"""
        CREATE (i:Integration 
            {{
                integrationType:'Aws',
                accessKey:'{access_key}', 
                secretKey:'{secret_key}',
                regionName: '{region_name}',
                regionName: '{bucket_name}'
            }})
        RETURN COUNT(i)
        """
        try:
            if graph.evaluate(cypher) == 1:
                data = "<span class='text-primary'>로그 수집/통합 설정 완료 </span>"
            else:
                raise Exception
        except Exception:
            data = "등록 실패"
        finally:
            return HttpResponse(data)

# ## Azure Cloud
# def integration_Azure(request):
#     if request.method == 'POST':
#         from azure.core.exceptions import ClientAuthenticationError
#         from azure.identity import ClientSecretCredential
#         from azure.mgmt.monitor import MonitorManagementClient
#         from datetime import datetime, timedelta
#         data = {}
#         access_key = request.POST['access_key'].encode('utf-8').decode('iso-8859-1')
#         if access_key == '':
#             data['class'] = 'btn btn-danger'
#             data['value'] = 'Subscription ID 를 입력해주세요'
#             return JsonResponse(data)
#         tenant_id = request.POST['tenant_id'].encode('utf-8').decode('iso-8859-1')
#         if tenant_id == '':
#             data['class'] = 'btn btn-danger'
#             data['value'] = 'tenant ID 를 입력해주세요'
#             return JsonResponse(data)
#         client_id = request.POST['client_id'].encode('utf-8').decode('iso-8859-1')
#         if client_id == '':
#             data['class'] = 'btn btn-danger'
#             data['value'] = 'Client ID 를 입력해주세요'
#             return JsonResponse(data)
#         secret_key = request.POST['secret_key'].encode('utf-8').decode('iso-8859-1')
#         if secret_key == '':
#             data['class'] = 'btn btn-danger'
#             data['value'] = 'Client Secret 을 입력해주세요'
#             return JsonResponse(data)
#         doc = {
#             'Azure_API.ACCESS_KEY': access_key,
#             'Azure_API.SECRET_KEY': secret_key
#         }
#         global collection
#         result = collection.find_one(doc)
#         if result:
#             data['class'] = 'btn btn-warning'
#             data['value'] = '이미 등록된 정보입니다.'
#         else:
#             # Configure the ClientSecretCredential instance.
#             credentials = ClientSecretCredential(tenant_id, client_id, secret_key)
#             # Instantiate a MonitorManagementClient instance.
#             monitor_client = MonitorManagementClient(credentials, access_key)
#             # Specify the time range for the activity logs.
#             end_time = datetime.utcnow()
#             start_time = end_time - timedelta(days=1)

#             # Define the filter for the activity logs.
#             filter_string = f"eventTimestamp ge {start_time.strftime('%Y-%m-%dT%H:%M:%S')}Z and eventTimestamp le {end_time.strftime('%Y-%m-%dT%H:%M:%S')}Z"
#             try:
#                 activity_logs = monitor_client.activity_logs.list(filter=filter_string)
#                 for log in activity_logs:
#                     break
#                 data['class'] = 'btn btn-success'
#                 data['value'] = ' ✓ 키 인증 및 Azure AD 서비스 사용 확인 완료!'
#                 data['modal'] = {}
#                 data['modal']['access_key'] = access_key
#                 data['modal']['tenant_id'] = tenant_id
#                 data['modal']['client_id'] = client_id
#                 data['modal']['secret_key'] = secret_key
#             except (ClientAuthenticationError, Exception):
#                 data['class'] = 'btn btn-danger'
#                 data['value'] = '인증 실패 (재시도)'
#             finally:
#                 return JsonResponse(data)
#         return JsonResponse(data)
#     data = {}
#     data['class'] = 'btn btn-danger'
#     data['value'] = '인증 실패 (재시도)'
#     return JsonResponse(data)

# def insert_Azure(request):
#     if request.method == 'POST':
#         access_key = request.POST['modal_access_key'].encode('utf-8').decode('iso-8859-1')
#         tenant_id = request.POST['modal_tenant_id'].encode('utf-8').decode('iso-8859-1')
#         client_id = request.POST['modal_client_id'].encode('utf-8').decode('iso-8859-1')
#         secret_key = request.POST['modal_secret_key'].encode('utf-8').decode('iso-8859-1')
#         global collection
#         doc = {'Azure_API': {
#             'ACCESS_KEY': access_key,
#             'SECRET_KEY': secret_key,
#             'TENANT_ID': tenant_id,
#             'CLIENT_ID': client_id
#         }}
#         try:
#             collection.insert_one(doc)
#             data = "<span class='text-primary'>로그 수집/통합 설정 완료 </span>"
#         except:
#             data = "등록 실패"
#         finally:
#             return HttpResponse(data)