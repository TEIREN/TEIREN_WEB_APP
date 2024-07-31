from django.http import JsonResponse
from django.conf import settings
import json

from .resource.aws import aws_check, aws_insert
from .resource.fortinet import fortinet_insert
from .resource.linux import linux_insert
from .resource.windows import windows_insert
from .resource.genians import genians_insert
from .resource.transmission import transmission_insert
from .resource.mssql import mssql_insert
from .resource.mysql import mysql_insert

from common.dockerHandler.handler import DockerHandler
from common.neo4j.handler import Neo4jHandler

# AWS
host = settings.NEO4J['HOST']
port = settings.NEO4J["PORT"]
username = settings.NEO4J['USERNAME']
password = settings.NEO4J['PASSWORD']

## Integration List
def list_integration(db_name):
    with Neo4jHandler() as neohandler:
        cypher = f"""
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
        """
        results = neohandler.run_data(database=db_name, query=cypher)
    # results['error'] = check_process_func(results['no'], results['container_id'])

    integration_list = [{'status': 'running' if data['isRunning'] == 1 else 'exited', **dict(data)} for data in results]
    return {'integrations': integration_list}

def check_process_func(no, container_id): # << 이건 뭐하는 함수임...?
    return True

def integration_check(request, equipment, logType):
    functionName = globals()[f'{equipment.lower()}_check']
    return functionName(request, logType)

def integration_insert(request, equipment):
    functionName = globals()[f'{equipment.lower()}_insert']
    return functionName(request)

## Integration delete
def delete_integration(request):
    secret_key = request.POST.get('secret_key')
    integration_type = request.POST.get('integration_type').title()
    access_key = request.POST.get('access_key')
    secret_key = request.POST.get('secret_key')
    region_name = request.POST.get('region_name')
    group_name = request.POST.get('group_name')
    log_type = request.POST.get('log_type')
    db_name = request.session.get('db_name')
    
    if not secret_key:
        return {'error': 'Please Enter Secret Key'}

    with Neo4jHandler() as neohandler:
        try:
            cypher = f"""
            MATCH (i:Integration {{
                    integrationType:'{integration_type}',
                    accessKey:'{access_key}',
                    secretKey:'{secret_key}',
                    regionName: '{region_name}',
                    groupName: '{group_name}',
                    logType: '{log_type}'
                }})
            RETURN COUNT(i) AS count
            """
            result = neohandler.run(database=db_name, query=cypher)
            if result['count'] == 1:
                cypher = f"""
                MATCH (i:Integration {{
                        integrationType:'{integration_type}',
                        accessKey:'{access_key}',
                        secretKey:'{secret_key}',
                        regionName: '{region_name}',
                        groupName: '{group_name}',
                        logType: '{log_type}'
                    }})
                DETACH DELETE i RETURN COUNT(i)
                """
                neohandler.run(database=db_name, query=cypher)
                return {'result': 'Deleted Registered Information'}
            else:
                raise Exception
        except Exception:
            return {'error': 'Failed to Delete Information. Please Check The Information'}

def container_trigger_on(neohandler, config, result):
    is_running = result["isRunning"]
    # 이미 실행중인 경우
    if is_running:
        return {
            'status': 'running',
            'containerId': result['container_id']
            }
    access_key = config['access_key']
    secret_key = config['secret_key']
    region_name = config['region_name']
    group_name = config['group_name']
    image_name = config['image_name']
    db_name = config['db_name']

    # docker hub에 main 브랜치의 이미지를 빌드시마다 항상 가져오기.
    # 현재는 고정값으로 넣어둠
    client = DockerHandler()
    logcollector_image_name = f"magarets/teiren-image:{image_name}_v_1.0"
    environment = {
        'AWS_ACCESS_KEY_ID': access_key,
        'AWS_SECRET_ACCESS_KEY': secret_key,
        'AWS_DEFAULT_REGION': region_name,
        'LOG_GROUP_NAME': group_name,
        'DATABASE_NAME': db_name
    }
    container = client.create_container(image_name=logcollector_image_name, 
                                        environment=environment)
    
    # 만약, cloudtrail 로그 수집기 요청이 들어오면, 탐지로직도 같이 실행
    if image_name == 'cloudtrail':
        detect_image_name = "magarets/teiren-image:detect_v_1.0"
        detect_environment = {
            'DATABASE_NAME': db_name
        }
        detect_container = client.create_container(image_name=detect_image_name,
                                                environment=detect_environment)
        
        cypher = f"""
        CREATE (i:Process)
        SET i.name = 'detect'
        SET i.isRunning = 1
        SET i.container_id = '{detect_container.id}'
        RETURN 1
        """
        neohandler.run(database=config['db_name'], query=cypher)
        print('detect start!')
    
    cypher = f"""
    MATCH (i:Integration)
    WHERE ID(i) = {result['id']}
    
    SET i.isRunning = 1
    SET i.container_id = '{container.id}'
    RETURN 1
    """
    # Integration 노드의 isRunning 속성을 1로 업데이트
    neohandler.run(database=config['db_name'], query=cypher)
    
    if result:
        return {
            'status': 'create', 
            'containerId': container.id
        }
    else:
        return {
            'status': 'fail', 
            'message': 'log collector dose not created'
        }
    
    
def container_trigger_off(neohandler, config, result):
    is_running = result['isRunning']
    container_id = result['container_id']
    
    if not is_running:
        result = {
            'status': 'fail',
            'message': f"{config['log_type']} log collector does not exist"
        }
        
        return result
    else:
        client = DockerHandler()
        res = client.stop_container(container_id)
        
        cypher = f"""
        MATCH (i:Integration)
        WHERE ID(i) = '{result['id']}'
        
        SET i.isRunning = 0
        SET i.container_id = 'None'
        RETURN 1
        """
        result = neohandler.run(database=config['db_name'], query=cypher)
        
        # cloudtrail 의 종료요청이라면, 탐지 프로세스도 같이 종료
        if config['image_name'] == 'cloudtrail':
            cypher = f"""
            MATCH (i:Process)
            WHERE i.name = 'detect'
            
            RETURN i.container_id AS id
            """
            result = neohandler.run(database=config['db_name'],query=cypher)
            res = client.stop_container(result['id'])
            cypher = f"""
            MATCH (i:Process)
            WHERE i.name = 'detect'
            
            SET i.isRunning = 0
            SET i.container_id = 'None'
            """
            result = neohandler.run(database=config['db_name'],query=cypher)
            print('detect stop!')
            
        if result:
            return {
                'status': 'delete',
                'message': res
            }
        else:
            return {
                'message': 'log collector delete fail'
            }

def container_trigger(request):
    """Running trigger for python script

    Args:
        request (bool): Return message successfully running or fail
    """
    secret_key = request.POST.get('secret_key')
    if secret_key == '':
        return {'error': 'Please Enter Secret Key'}
    try:
        access_key = request.POST.get('access_key')
        region_name = request.POST.get('region_name')
        log_type = request.POST.get('log_type') # log type (ex: cloudtrail, dns, elb ...)
        group_name = request.POST.get('group_name')
        image_name = f'{log_type}'
        db_name = request.session.get('db_name')
        
        print('=================')
        print(log_type)
        print(image_name)
        print(db_name)
        cypher = f"""
        MATCH (i:Integration{{
            accessKey: '{access_key}',
            secretKey: '{secret_key}',
            regionName: '{region_name}',
            groupName: '{group_name}',
            imageName: '{image_name}',
            logType: '{log_type}'
        }})
        RETURN COUNT(i) AS count, ID(i) AS id, i.isRunning AS isRunning, i.container_id AS container_id"""
        with Neo4jHandler() as neohandler:
            result = neohandler.run(database=db_name, query=cypher)
            print(f"count: {result['count']}")
            print(f"id: {result['id']}")
            print(f"isRunning: {result['isRunning']}")
            
            if 1 != result['count']:
                return {'error': 'Wrong Information. Please Check The Information'}  
            
            config = {
                'access_key': access_key,
                'secret_key': secret_key,
                'region_name': region_name,
                'group_name': group_name,
                'image_name': image_name,
                'db_name': request.session.get('db_name')
            }
            
            is_collection_on = int(request.POST.get('on_off'))
            # log collector ON
            if is_collection_on == 1:
                result = container_trigger_on(neohandler=neohandler, config=config, result=result)
                return result
            # log collector OFF
            else:
                result = container_trigger_off(neohandler=neohandler, config=config, result=result)
                return result
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)