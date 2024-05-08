from django.http import JsonResponse
from py2neo import Graph
from django.conf import settings
import json
from .resource.aws import aws_check, aws_insert
from common.dockerHandler.handler import DockerHandler

# AWS
host = settings.NEO4J['HOST']
port = settings.NEO4J["PORT"]
username = settings.NEO4J['USERNAME']
password = settings.NEO4J['PASSWORD']
graph = Graph(f"bolt://{host}:{port}", auth=(username, password))

## Integration List
def list_integration():
    results = graph.run(f"""
    MATCH (i:Integration)
    RETURN
        toLower(i.integrationType) AS integrationType,
        i.accessKey AS accessKey,
        i.regionName AS regionName,
        i.logType AS logType,
        i.groupName AS groupName,
        i.isRunning AS isRunning,
        i.container_id as container_id,
        id(i) as no
    """)
    response = []
    for result in results:
        data = dict(result.items())
        data['error'] = check_process_func(data['no'], data['container_id'])        
        response.append(data)
    return {'integrations': response}

def check_process_func(no, container_id):
    return True

def integration_check(request, equipment, logType):
    functionName = globals()[f'{equipment.lower()}_check']
    return functionName(request, logType)

def integration_insert(request, equipment):
    functionName = globals()[f'{equipment.lower()}_insert']
    return functionName(request)

## Integration delete
def delete_integration(request):
    if request['secret_key'] == '':
        return {'error': 'Please Enter Secret Key'}
    # return {'result': str(request)}
    cypher = f"""
    MATCH (i:Integration {{
            integrationType:'{request['integration_type'].title()}',
            accessKey:'{request['access_key']}',
            secretKey:'{request['secret_key']}',
            regionName: '{request['region_name']}',
            groupName: '{request['group_name']}',
            logType: '{request['log_type']}'
        }})
    """
    try:
        if 1 == graph.evaluate(f"{cypher} RETURN COUNT(i)"):
            graph.evaluate(f"{cypher} DETACH DELETE i RETURN COUNT(i)")
            return {'result': 'Deleted Registered Information'}
        else:
            raise Exception
    except Exception:
        return {'error': 'Failed to Delete Information. Please Check The Information'}

def container_trigger_on(integration_node, aws_config):
    is_running = integration_node["isRunning"]
    access_key = aws_config.get('access_key')
    secret_key = aws_config.get('secret_key')
    region_name = aws_config.get('region_name')
    group_name = aws_config.get('group_name')
    image_name = aws_config.get('image_name')
    
    if is_running:
        result = {
            'status': 'running',
            'containerId': integration_node['container_id']
            }
        
        return result
    else:
        # docker hub에 main 브랜치의 이미지를 빌드시마다 항상 가져오기.
        # 현재는 고정값으로 넣어둠
        client = DockerHandler()
        logcollector_image_name = f"magarets/teiren-image:{image_name.split('-')[0]}_v_1.0"
        
        environment = {
            'AWS_ACCESS_KEY_ID': access_key,
            'AWS_SECRET_ACCESS_KEY': secret_key,
            'AWS_DEFAULT_REGION': region_name,
            'LOG_GROUP_NAME': group_name
        }
        container = client.create_container(image_name=logcollector_image_name, 
                                            environment=environment)
        # Integration 노드의 isRunning 속성을 1로 업데이트
        integration_node['isRunning'] = 1
        integration_node['container_id'] = container.id
        graph.push(integration_node)
        
        result = { 
            'status': 'create', 
            'containerId': container.id 
            }
        
        return result
    
def container_trigger_off(integration_node, aws_config):
    is_running = integration_node['isRunning']
    container_id = integration_node['container_id']
    
    if not is_running:
        result = {
            'status': 'none',
            'containerId': integration_node['container_id']
            }
        
        return result
    else:
        client = DockerHandler()
        res = client.stop_container(container_id)
        res = client.remove_container(container_id)
        result = {
            'status': 'delete',
            'message': res
        }
        
        return result

def container_trigger(request):
    """Running trigger for python script

    Args:
        request (bool): Return message successfully running or fail
    """
    secret_key = request.get('secret_key')
    if secret_key == '':
        return {'error': 'Please Enter Secret Key'}
    try:
        access_key = request.get('access_key')
        region_name = request.get('region_name')
        log_type = request.get('log_type') # log type (ex: cloudtrail, dns, elb ...)
        group_name = request.get('group_name')
        image_name = f'{log_type}-image'
        if 1 != graph.evaluate(f"""
        MATCH (i:Integration{{
            accessKey: '{access_key}',
            secretKey: '{secret_key}',
            regionName: '{region_name}',
            groupName: '{group_name}',
            imageName: '{image_name}',
            logType: '{log_type}'
        }})
        RETURN COUNT(i)
        """):
            return {'error': 'Wrong Information. Please Check The Information'}     
        # isRunning을 통해, 현재 log type의 group name을 수집하는 로그 수집기가 동작중인지 확인
        integration_node = graph.nodes.match("Integration", 
                                accessKey=access_key, 
                                secretKey=secret_key, 
                                regionName=region_name,
                                logType=log_type,
                                groupName=group_name
                                ).first()
        aws_config = {
            'access_key': access_key,
            'secret_key': secret_key,
            'region_name': region_name,
            'group_name': group_name,
            'image_name': image_name
        }
        is_collection_on = int(request.get('on_off'))
        # log collector ON
        if is_collection_on == 1:
            result = container_trigger_on(integration_node, aws_config)
            
            return result         
        # log collector OFF
        else:
            result = container_trigger_off(integration_node, aws_config)    
            
            return result
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)

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