# local
import json
import requests

# django
from pathlib import Path
from django.shortcuts import render, HttpResponse, redirect
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib.auth.signals import user_logged_out, user_logged_in
from django.dispatch import receiver

# 3rd party
from py2neo import Graph

# LOCAL
# graph = Graph("bolt://127.0.0.1:7687", auth=('neo4j', 'teiren001'))

# NCP
# host = settings.NEO4J_HOST
# port = settings.NEO4J_PORT
# password = settings.NEO4J_PASSWORD
# username = settings.NEO4J_USERNAME

# AWS
host = settings.NEO4J['HOST']
port = settings.NEO4J["PORT"]
username = settings.NEO4J['USERNAME']
password = settings.NEO4J['PASSWORD']
graph = Graph(f"bolt://{host}:{port}", auth=(username, password))

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = BASE_DIR / 'staticfiles'

# Create your tests here.
def main_test(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0] # 'X-Forwarded-For' header can contain multiple IP addresses
    else:
        ip = request.META.get('REMOTE_ADDR')
    try:
        xxx = requests.get('http://169.254.169.254/latest/meta-data/public-ipv4', timeout=2).text
    except requests.exceptions.RequestException:
        xxx = '127.0.0.1'
    context = {'test': ip+'---'+xxx}
    
    return render(request, 'testing/test.html', context)

def test_ajax(request):
    return HttpResponse(str(dict(request.POST)))

from testing.dockerHandler.handler import DockerHandler
def trigger(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            access_key = data.get('access_key')
            secret_key = data.get('secret_key')
            region_name = data.get('region_name')
            log_type = data.get('log_type') # cloudtrail, dns, elb ...
            group_name = data.get('group_name')
            image_name = f'{log_type}-image'
            
            # 위 3가지 속성에 해당하는 노드의 "isRunning" 속성을 py2neo를 이용해서 가져오기
            pass
        
            # isRunning을 통해, 현재 로그 수집기가 동작중인지 확인
            integration_node = graph.nodes.match("Integration", 
                                    accessKey=access_key, 
                                    secretKey=secret_key, 
                                    regionName=region_name,
                                    logType=log_type,
                                    groupName=group_name,
                                    imageName=image_name
                                    ).first()
            is_running = integration_node["isRunning"]
            if is_running:
                result = {'message': '로그 수집기가 이미 동작중입니다.'}
                return JsonResponse(result)
            else:
                # docker hub에 main 브랜치의 이미지를 빌드시마다 항상 가져오기.
                # 현재는 고정값으로 넣어둠
                client = DockerHandler()
                logcollector_image_name = image_name
                environment = {
                    'AWS_ACCESS_KEY_ID': access_key,
                    'AWS_SECRET_ACCESS_KEY': secret_key,
                    'AWS_DEFAULT_REGION': region_name
                }
                container = client.create_container(image_name=logcollector_image_name, 
                                                    environment=environment)
                # Integration 노드의 isRunning 속성을 1로 업데이트
                integration_node['isRunning'] = 1
                graph.push(integration_node)
                
                result = {'message': f'인스턴스가 성공적으로 저장되었습니다. 인스턴스 id: {container.id}'}
                print(f"access_key: {access_key}")
                print(f"secret_key: {secret_key}")
                print(f"region_name: {region_name}")
                print(f"log_type: {log_type}")
                print(f"group_name: {group_name}")
                print(f"image_name: {image_name}")
                return JsonResponse(result)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    else:
        return HttpResponseBadRequest('Invalid request method')
    # docker_handler = DockerHandler()
    # client = docker_handler.client
    
    # environment = {
    #     'AWS_ACCESS_KEY_ID': 'your_access_key',
    #     'AWS_SECRET_ACCESS_KEY': 'your_secret_key',
    #     'AWS_DEFAULT_REGION': 'your_region_name'
    # }
    
    # # handling
    # client.containers.run(
    #     'image-name',
    #     detach=True,
    #     environment=environment,
    # )

def running_trigger(request):
    """Running trigger for python script

    Args:
        request (bool): Return message successfully running or fail
    """
    request_dict = {
        'access_key': 'test_access_key',
        'secret_key': 'test_secret_key',
        'region_name': 'test_region_name',
        'bucket_name': 'test_bucket_name'
    }
    print(request_dict)

    return render(request, 'testing/trigger.html', {'request_dict': request_dict})

def test_400(request, exception=None):
    return render(request, '404page.html', status=404)

def dashboard(request):
    return render(request, 'testing/integration.html')

import boto3

def create_iam_user_with_policy(account_key, secret_key, user_name):
    error_message = {}
    
    try:
        iam = boto3.client('iam', 
                        aws_access_key_id=account_key, 
                        aws_secret_access_key=secret_key, 
                        region_name='us-east-1')
        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "cloudtrail:DescribeTrails",
                        "cloudtrail:GetTrailStatus",
                        "cloudwatch:Describe*",
                        "ec2:Describe*",
                        "elasticloadbalancing:Describe*",
                        "route53:List*",
                        "vpc:Describe*"
                    ],
                    "Resource": "*"
                }
            ]
        }
        # Iam User 새로 생성
        try:
            user = iam.create_user(UserName=user_name)
            print(f"IAM 사용자 생성됨: {user['User']['UserName']}")
        except:
            error_message['createIamUserStatus'] = 'Fail'            
        
        # IAM 정책생성
        try:
            policy_name = f"{user_name}-Policy"
            policy = iam.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document)
            )
            print(f"IAM 정책 생성됨: {policy['Policy']['PolicyName']}")
        except:
            error_message['createIamPolicy'] = 'Fail'

        # 정책을 사용자에게 부여
        try:
            iam.attach_user_policy(
                UserName=user_name,
                PolicyArn=policy['Policy']['Arn']
            )
            print(f"정책이 사용자 {user_name}에게 부여됨")
        except:
            error_message['attachPolicy'] = 'Fail'

        try:
            # 새로운 액세스키 생성
            access_key_data = iam.create_access_key(UserName=user_name)
        except:
            error_message['createAccessKey'] = 'Fail'
            
        access_key = access_key_data['AccessKey']['AccessKeyId']
        secret_key = access_key_data['AccessKey']['SecretAccessKey']

        return access_key, secret_key, error_message
    except ClientError as e:
        print(e)
        error_message['message'] = 'Fail to Create IAM Policy User'
        return None, None, error_message
    
def create_iam_policy(request):
    if request.method == "POST":
        root_access_key = request.POST.get('accessKey')
        root_secret_key = request.POST.get('secretKey')
        user_name = request.POST.get('userName')
        
        print(root_access_key, root_secret_key, user_name)
        try:
            # Create aws IAM policy user
            created_access_key, created_secret_key, error_message = create_iam_user_with_policy(root_access_key, root_secret_key, user_name)
            
            if created_access_key is None or created_secret_key is None:
                return JsonResponse({'status': 'Error', 'message': 'Failed to create IAM user'})
            elif not error_message:
                # Success to create IAM policy user
                response = {
                    'status': 'Success',
                    'message': 'IAM User created successfully.',
                    'accessKey': created_access_key,
                    'secretKey': created_secret_key,
                    'userName': user_name
                }
                return JsonResponse(response)
            else:
                # Fail to create IAM policy user
                return JsonResponse(error_message)
        except ClientError as e:
            print(e)
            return JsonResponse({'status': 'Error', 'message': 'Failed to create IAM user'})
    else:
        return JsonResponse({'status': 'Error', 'message': 'Invalid request'})


from botocore.exceptions import ClientError
def check_aws_credentials(access_key, secret_key):
    try:
        # AWS 클라이언트 생성
        iam = boto3.client(
            'iam',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name='your-region'  # 적절한 AWS 리전으로 대체
        )

        # 간단한 요청 수행, 예를 들어 현재 사용자의 정보를 가져옴
        user = iam.get_user()
        return True, user['User']
    except ClientError as e:
        # 오류 발생 시
        print(e)
        return False, None
        

def cloudformation(request):
    if request.method == "POST":

        access_key = request.POST.get('accessKey')
        secret_key = request.POST.get('secretKey')

        print("Access Key:", access_key)
        print("Secret Key:", secret_key)

        is_aws_user, aws_user = check_aws_credentials(access_key, secret_key)
        result = {
            'isAwsUser': is_aws_user,
            'User': aws_user
        }
        result['status'] = 'Success'
        return JsonResponse(result)
    else:
        return render(request, 'testing/cloudformation.html')
    
def login_(request):
    return render(request, 'testing/login.html')

def register_(request):
    return render(request, 'registration/activation_failure.html')


    