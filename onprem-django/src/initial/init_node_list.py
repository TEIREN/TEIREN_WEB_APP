all_merge_node_query = [
    # ===== ALL ===== #
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'abnormal_time_api_call',
            ruleComment : 'API호출 시간이 규정 외 일 경우',
            eventType : 'AwsApiCall',
            userIdentity_type:'IAMUser',
            eventTime_start : 1,
            eventTime_end : 6,
            level : 1,
            on_off : 1,
            ruleType : 'default'
        })
    '''
]
iam_merge_node_query = [
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'create_login_profile',
            ruleComment : 'Create Login Profile API를 사용하여 IAM 사용자의 비밀번호를 생성',
            eventName : 'CreateLoginProfile',
            eventType : 'AwsApiCall',
            eventSource : 'iam.amazonaws.com',
            level : 1,
            on_off : 1,
            ruleType : 'default'
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'python_cli_attachPolicy',
            ruleComment : 'IAM사용자가 python api호출을 통해 전체관리자권한 부여',
            eventName: 'AttachUserPolicy',
            userIdentity_type : 'IAMUser',
            requestParameters_policyArn : 'AdministratorAccess',
            userAgent : 'Boto3',
            eventSource: 'iam.amazonaws.com',
            on_off : 1,
            level: 3,
            ruleType: 'default'
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'delete_role_by_iam',
            ruleComment : 'IAM사용자가 기존 인스턴스 프로필에 할당된 role 삭제',
            eventName: 'RemoveRoleFromInstanceProfile',
            userIdentity_type : 'IAMUser',
            eventSource: 'iam.amazonaws.com',
            on_off : 1,
            level: 1,
            ruleType: 'default'
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'activate_access_key',
            ruleComment : 'iam 사용자가 비정상적인 방식으로 access key 활성화',
            eventName: 'UpdateAccessKey',
            userIdentity_type : 'IAMUser',
            requestParmeters_status : 'Active',
            eventSource: 'iam.amazonaws.com',
            on_off : 1,
            level: 1,
            ruleType: 'default'
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'put_high_policy_to_user',
            ruleComment : '사용자에게 aws환경에 대한 높은 수준의 권한 부여',
            eventName: 'PutUserPolicy',
            requestParameters_policyDocument:['"Action":"*"', '"Resource":"*"'],
            requestParameters_policyDocument_Effect : '"Effect":"Allow"',
            eventSource: 'iam.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType: 'default'
        })
    ''']
ec2_merge_node_query = [
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'open_database_port',
            ruleComment : '데이터베이스 서비스와 연결된 포트에서 aws security group을 여는 경우 탐지',
            eventName : 'AuthorizeSecurityGroupIngress',
            portList : [1433, 3306, 5432, 5984, 6984, 6379, 9200, 27017],
            on_off : 1,
            eventSource: 'ec2.amazonaws.com',
            level: 3,
            ruleType: 'default'
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'security_group_permission_all',
            ruleComment : 'AuthorizeSecurityGroupIngress API를 사용하여 SECURITY GRUOP을 공개',
            eventName : 'AuthorizeSecurityGroupIngress',
            cidrIp : ['0.0.0.0/0', '::/0'],
            on_off : 1,
            eventSource: 'ec2.amazonaws.com',
            level: 3,
            ruleType: 'default'
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'delete_ec2_log',
            ruleComment : 'ec2 로그 삭제 api가 호출될 경우',
            eventName : 'DeleteFlowLogs',
            eventSource: 'ec2.amazonaws.com',
            on_off : 1,
            level: 3,
            ruleType: 'default'
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'get_pwd_data',
            ruleComment : '실행 중인 윈도우 인스턴스의 비밀번호 검색 및 출력',
            eventName : 'GetPasswordData',
            on_off : 1,
            eventSource: 'ec2.amazonaws.com',
            level: 2,
            ruleType: 'default'
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'import_ec2_keypair',
            ruleComment : 'ec2 인스턴스에서 키 쌍 생성 후 퍼블릭 키 획득',
            eventName : 'ImportKeyPair',
            on_off : 1,
            eventSource: 'ec2.amazonaws.com',
            level: 3,
            ruleType: 'default'
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'able_instance_api_termination',
            ruleComment : '콘솔, cli, api를 통해 인스턴스 종료할 수 있도록 변경',
            eventName : 'ModifyInstanceAttribute',
            requestParameters_disableApiTermination_value : false,
            on_off : 1,
            eventSource: 'ec2.amazonaws.com',
            level: 2,
            ruleType: 'default'
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'ec2_list_buckets',
            ruleComment : 'ec2 인스턴스로부터 s3 버킷 목록 조회 요청 이벤트 발생',
            eventName : 'ListBuckets',
            userIdentity_type : 'AssumedRole',
            userIdentity_principalId : 'i-',
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType: 'default'
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'run_high_cpu_instance',
            ruleComment : 'aws 환경 내 인스턴스보다 과도하게 높은 성능의 cpu ec2 인스턴스 생성 행위',
            eventName : 'RunInstances',
            requestParameters_instanceType : 10,
            on_off : 1,
            eventSource: 'ec2.amazonaws.com',
            level: 2,
            ruleType: 'default'
        })
    ''']
s3_merge_node_query = [
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'delete_bucket_cloudtrail',
            ruleComment : 'cloudtrail 로그 관련 s3 버킷 삭제',
            eventName : 'DeleteBucket',
            requestParameters_bucketName : 'cloudtrail',
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 3,
            ruleType: 'default'
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'disable_s3_logging',
            ruleComment : '버킷에 대한 s3 서버 액세스 로깅 비활성화',
            eventName : 'PutBucketLogging',
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 1,
            ruleType: 'default'
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'iam_allow_s3_global_allUsers',
            ruleComment : 'iam사용자가 버킷 액세스 정책 변경을 통해 모든 aws 사용자에게 s3 버킷에 대한 퍼블릭 액세스 권한 부여',
            eventName : 'PutBucketAcl',
            userIdentity_type : 'IAMUser',
            accessControlList : ['global', 'AllUsers'],
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType: 'default'
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'create_s3_public_acls_point',
            ruleComment : 's3 버킷에 대한 퍼블릭 액세스 포인트 생성',
            eventName : 'CreateAccessPoint',
            publicAccessBlockConfiguration : false,
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 1,
            ruleType: 'default'
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 's3_bucketAcl_public',
            ruleComment : 's3 Bucket Acl Storage를 public으로 변경하는 경우',
            eventName : 'PutBucketAcl',
            `requestParameters_x-amz-acl` : 'public',
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 'medium',
            ruleType: 'default'
        })
    ''']
cloudtrail_merge_node_query = [
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'delete_trail',
            ruleComment : 'cloudtrail 로그 기록 삭제',
            eventName : 'DeleteTrail',
            eventSource: 'cloudtrail.amazonaws.com',
            on_off : 1,
            level: 3,
            ruleType: 'default'
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'stop_logging',
            ruleComment : 'cloudtrail 로그 기록 중단',
            eventName : 'StopLogging',
            eventSource: 'cloudtrail.amazonaws.com',
            on_off : 1,
            level: 3,
            ruleType: 'default'
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'create_trail_event_selector',
            ruleComment : 'AWS 로그 서비스인 CloudTrail에서 이벤트 필터링을 담당하는 event selector 생성 이벤트 발생',
            eventName : 'PutEventSelectors',
            eventSource: 'cloudtrail.amazonaws.com',
            on_off : 1,
            level: 1,
            ruleType: 'default'
        })
    ''']
rds_merge_node_query = [
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'promote_read_replica',
            ruleComment : 'iam 사용자가 비정상적 방식으로 읽기 전용 복제본 db 인스턴스를 독립 실행형 db 인스턴스로 승격',
            eventName : 'PromoteReadReplica',
            userIdentity_type : 'IAMUser',
            eventSource: 'rds.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType: 'default'
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'db_public_access',
            ruleComment : 'DB 인스턴스에 공개적으로 접근 가능하도록 수정',
            eventName : 'ModifyDBInstance',
            responseElements_publiclyAccessible : true,
            eventSource: 'rds.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType: 'default'
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'rds_delete_protect_disable',
            ruleComment : 'RDS 인스턴스 삭제 방지 기능 해제',
            eventName : ['ModifyDBCluster', 'ModifyDBInstance'],
            responseElements_deletionProtection : false,
            eventSource: 'rds.amazonaws.com',
            on_off : 1,
            level: '1',
            ruleType: 'default'
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'delete_db_cluster',
            ruleComment : 'IAM 사용자가 RDS DB 클러스터 또는 인스턴스 삭제',
            eventName : ['DeleteDBCluster', 'DeleteDBInstance'],
            userIdentity_type : 'IAMUser',
            eventSource: 'rds.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType: 'default'
        })
    ''']
ecs_merge_node_query = [
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'create_fargate_curl_task_definition',
            ruleComment : '다른 주소로 연결되는 command를 호함해 컨테이너 자동시작 task definition 생성',
            eventName: 'RegisterTaskDefinition',
            requestParameters_containerDefinitions_command : 'curl',
            requestParameters_requiresCompatibilities : 'FARGATE',
            eventSource : 'ecs.amazonaws.com',
            level : 3,
            on_off : 1
        })
    ''']
cloudwatch_merge_node_query = [
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'disable_alarm_actions',
            ruleComment : 'cloudwatch 경보 삭제',
            eventName: ['DeleteAlarms', 'DisableAlarmActions'],
            on_off : 1,
            eventSource : 'monitoring.amazonaws.com',
            level : 'high'
        })
    '''
]
signin_merge_node_query = [
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'console_login_without_mfa',
            ruleComment : 'root를 포함한 사용자가 MFA 없이 로그인',
            eventName: 'ConsoleLogin',
            additionalEventData_MFAUsed : 'No',
            on_off : 1,
            eventSource : 'signin.amazonaws.com',
            level : 1
        })
    '''
]
cognito_merge_node_query = [
    
]
kms_merge_node_query = [
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'schedule_kms_key_deletion',
            ruleComment : 'key가 비정상적인 삭제 예약 설정된 경우',
            eventName: 'ScheduleKeyDeletion',
            on_off : 1,
            eventSource : 'kms.amazonaws.com',
            level : 2
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'disable_kms_key',
            ruleComment : 'key가 비정상적인 방식으로 비활성화 된 경우',
            eventName: 'DisableKey',
            on_off : 1,
            eventSource : 'kms.amazonaws.com',
            level : 2
        })
    '''
]
secretsManager_merge_node_query = [
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'get_secret_value',
            ruleComment : 'database에 대한 암호 조회',
            eventName : 'GetSecretValue',
            eventSource: 'secretsmanager.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType: 'default'
        })
    '''
]
init_merge_detect_query = []
merge_node_list = ['all_merge_node_query',
                   'iam_merge_node_query',
                   'ec2_merge_node_query',
                   's3_merge_node_query',
                   'cloudtrail_merge_node_query',
                   'rds_merge_node_query',
                   'ecs_merge_node_query',
                   'cloudwatch_merge_node_query',
                   'signin_merge_node_query',
                   'cognito_merge_node_query',
                   'kms_merge_node_query',
                   'secretsManager_merge_node_query']
# extending query list
for query_name in merge_node_list:
    current_list = globals().get(query_name)
    init_merge_detect_query.extend(current_list)