import json
from common.dockerHandler.handler import DockerHandler
from common.neo4j.handler import Neo4jHandler
from django.http import JsonResponse


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