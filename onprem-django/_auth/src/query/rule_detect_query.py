rule_detect_all = [
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'abnormal_time_api_call',
            ruleComment : 'API호출 시간이 규정 외 일 경우',
            eventType : 'AwsApiCall',
            userIdentity_type:'IAMUser',
            eventTime_start : 2,
            eventTime_end : 5,
            level : 1,
            on_off : 1,
                ruleType : 'default',
                ruleClass : 'static',
                query: "MATCH (rule:Rule:Aws {
            ruleName : 'abnormal_time_api_call',
            ruleComment : 'API호출 시간이 규정 외 일 경우',
            eventType : 'AwsApiCall',
            userIdentity_type:'IAMUser',
            eventTime_start : 2,
            eventTime_end : 5,
            level : 1,
            on_off : 1,
                ruleType : 'default',
                ruleClass : 'static'
            })
        WITH rule
        CALL apoc.do.when(
        rule.eventTime_start > rule.eventTime_end,
            'MATCH (log:Log:Aws) WITH datetime(log.eventTime).epochSeconds+32400 as time,log,rule WITH datetime({epochSeconds:time}) as dt,log WHERE rule.eventTime_start <= dt.hour < 24 AND 0 <= dt.hour < rule.eventTime_end and log.userIdentity_type = rule.userIdentity_type
        RETURN log',
        'MATCH (log:Log:Aws) WITH datetime(log.eventTime).epochSeconds+32400 as time,log,rule WITH datetime({epochSeconds:time}) as dt,log WHERE dt.hour >= rule.eventTime_start AND dt.hour <= rule.eventTime_end and log.userIdentity_type = rule.userIdentity_type
        RETURN log',
        {rule : rule}
        ) YIELD value
        WITH value.log as log, rule
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'linux_api_call',
            ruleComment : 'linux 가상머신 시스템에서 api 호출',
            userAgent : 'linux',
            eventType : 'AwsApiCall',
            level : 1,
            on_off : 1,
            ruleType : 'default',
            ruleClass : 'static',
            query:"MATCH (rule:Rule:Aws {
            ruleName : 'linux_api_call',
            ruleComment : 'linux 가상머신 시스템에서 api 호출',
            userAgent : 'linux',
            eventType : 'AwsApiCall',
            level : 1,
            on_off : 1,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE toLower(log.userAgent) CONTAINS rule.userAgent
            AND log.eventType = rule.eventType
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'north_korea_aws_access',
            ruleComment : '북한 ip 대역에서 aws 환경에 접근',
            country : 'KP',
            level : 3,
            on_off : 1,
            ruleType : 'default',
            ruleClass : 'static',
            query:"MATCH (rule:Rule:Aws {
            ruleName : 'north_korea_aws_access',
            ruleComment : '북한 ip 대역에서 aws 환경에 접근',
            country : 'KP',
            level : 3,
            on_off : 1,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.country = rule.country
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    '''
]
rule_detect_iam = [
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'create_aws_account_role',
            ruleComment : 'IAM이 아닌 새로운 Accoun에게 역할 추가',
            eventName: 'CreateRole',
            eventSource: 'iam.amazonaws.com',
            requestParameters_assumeRolePolicyDocument : '.*?"AWS":"\d{12}".*?',
            on_off : 1,
            level: 1,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'create_aws_account_role',
            ruleComment : 'IAM이 아닌 새로운 Accoun에게 역할 추가',
            eventName: 'CreateRole',
            eventSource: 'iam.amazonaws.com',
            requestParameters_assumeRolePolicyDocument : '.*?\\\"AWS\\\":\\\"\d{12}\\\".*?',
            on_off : 1,
            level: 1,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND log.requestParameters_assumeRolePolicyDocument =~ rule.requestParameters_assumeRolePolicyDocument
            AND not log.requestParameters_assumeRolePolicyDocument contains '622751588873'
            AND log.eventSource = rule.eventSource
            AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'get_ssh_public_key_cli',
            ruleComment : 'cli를 통해 지정된 SSH 공개 키 검색',
            eventName: 'GetSSHPublicKey',
            userAgent : 'cli',
            eventSource: 'iam.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static',
            query:"MATCH (rule:Rule:Aws {
            ruleName : 'get_ssh_public_key_cli',
            ruleComment : 'cli를 통해 지정된 SSH 공개 키 검색',
            eventName: 'GetSSHPublicKey',
            userAgent : 'cli',
            eventSource: 'iam.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND log.userIdentity_type CONTAINS rule.userIdentity_type
            AND toLower(log.userAgent) contains rule.userAgent
            AND log.eventSource = rule.eventSource
            AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'delete_role_permission_boundary',
            ruleComment : '지정된 IAM 역할에 대한 권한 경계 삭제',
            eventName: 'DeleteRolePermissionsBoundary',
            eventSource: 'iam.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static',
            query:"MATCH (rule:Rule:Aws {
            ruleName : 'delete_role_permission_boundary',
            ruleComment : '지정된 IAM 역할에 대한 권한 경계 삭제',
            eventName: 'DeleteRolePermissionsBoundary',
            eventSource: 'iam.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND log.eventSource = rule.eventSource
            AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'attach_user_full_access_policy',
            ruleComment : 'IAM 사용자에게 특정 서비스에 대한 전체 액세스 권한 부여',
            requestParameters_policyArn: 'FullAccess',
            eventSource: 'iam.amazonaws.com',
            eventName: 'AttachUserPolicy',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'attach_user_full_access_policy',
            ruleComment : 'IAM 사용자에게 특정 서비스에 대한 전체 액세스 권한 부여',
            requestParameters_policyArn: 'FullAccess',
            eventSource: 'iam.amazonaws.com',
            eventName: 'AttachUserPolicy',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND log.requestParameters_policyArn CONTAINS rule.requestParameters_policyArn
            AND log.eventSource = rule.eventSource
            AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'deactivate_mfa_iam',
            ruleComment : 'IAM사용자가 지정된 MFA 디바이스 비활성화하고 기존에 활성화된 사용자 연결에서 제거',
            eventName: ['DeactivateMFADevice', 'DeleteVirtualMFADevice'],
            eventSource: 'iam.amazonaws.com',
            userIdentity_type : 'IAMUser',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'deactivate_mfa_iam',
            ruleComment : 'IAM사용자가 지정된 MFA 디바이스 비활성화하고 기존에 활성화된 사용자 연결에서 제거',
            eventName: ['DeactivateMFADevice', 'DeleteVirtualMFADevice'],
            eventSource: 'iam.amazonaws.com',
            userIdentity_type : 'IAMUser',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName in rule.eventName
            AND log.userIdentity_type CONTAINS rule.userIdentity_type
            AND log.eventSource = rule.eventSource
            AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
        ruleName : 'create_login_profile',
        ruleComment : 'Create Login Profile API를 사용하여 IAM 사용자의 비밀번호를 생성',
        eventName : 'CreateLoginProfile',
        eventType : 'AwsApiCall',
        eventSource : 'iam.amazonaws.com',
        level : 1,
        on_off : 1,
        ruleType : 'default',
        ruleClass : 'static',
        query:"MATCH (rule:Rule:Aws {
        ruleName : 'create_login_profile',
        ruleComment : 'Create Login Profile API를 사용하여 IAM 사용자의 비밀번호를 생성',
        eventName : 'CreateLoginProfile',
        eventType : 'AwsApiCall',
        eventSource : 'iam.amazonaws.com',
        level : 1,
        on_off : 1,
        ruleType : 'default',
        ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName = rule.eventName
            and log.eventType = rule.eventType
            AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
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
            ruleType : 'default',
            ruleClass : 'static',
            query:"MATCH (rule:Rule:Aws {
            ruleName : 'python_cli_attachPolicy',
            ruleComment : 'IAM사용자가 python api호출을 통해 전체관리자권한 부여',
            eventName: 'AttachUserPolicy',
            userIdentity_type : 'IAMUser',
            requestParameters_policyArn : 'AdministratorAccess',
            userAgent : 'Boto3',
            eventSource: 'iam.amazonaws.com',
            on_off : 1,
            level: 3,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND log.userIdentity_type CONTAINS rule.userIdentity_type
            AND log.requestParameters_policyArn CONTAINS rule.requestParameters_policyArn
            AND log.userAgent CONTAINS rule.userAgent
            AND log.eventSource = rule.eventSource
            AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'activate_access_key',
            ruleComment : 'iam 사용자가 다른 사용자 access key 활성화',
            eventName1 : 'UpdateAccessKey',
            eventName2 : 'CreateAccessKey',
            userIdentity_type : 'IAMUser',
            requestParameters_status : 'Active',
            responseElements_accessKey_status :'Active',
            eventSource: 'iam.amazonaws.com',
            on_off : 1,
            level: 1,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'activate_access_key',
            ruleComment : 'iam 사용자가 다른 사용자 access key 활성화',
            eventName1 : 'UpdateAccessKey',
            eventName2 : 'CreateAccessKey',
            userIdentity_type : 'IAMUser',
            requestParameters_status : 'Active',
            responseElements_accessKey_status :'Active',
            eventSource: 'iam.amazonaws.com',
            on_off : 1,
            level: 1,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE (log.eventName = rule.eventName1 AND log.eventSource = rule.eventSource
            AND log.userIdentity_type = rule.userIdentity_type
            AND log.requestParameters_status = rule.requestParameters_status
            AND NOT log.userIdentity_arn CONTAINS log.requestParameters_userName)
        OR (log.eventName = rule.eventName2 AND log.eventSource = rule.eventSource
            AND log.userIdentity_type = rule.userIdentity_type
            AND log.responseElements_accessKey_status = rule.responseElements_accessKey_status
            AND NOT log.userIdentity_arn CONTAINS log.requestParameters_userName)
            AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)
        "
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
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'put_high_policy_to_user',
            ruleComment : '사용자에게 aws환경에 대한 높은 수준의 권한 부여',
            eventName: 'PutUserPolicy',
            requestParameters_policyDocument:['\\\"Action\\\":\\\"*\\\"', '\\\"Resource\\\":\\\"*\\\"'],
            requestParameters_policyDocument_Effect : '\\\"Effect\\\":\\\"Allow\\\"',
            eventSource: 'iam.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND log.eventSource = rule.eventSource
            AND any(policy in rule.requestParameters_policyDocument where log.requestParameters_policyDocument contains policy)
            AND log.requestParameters_policyDocument contains rule.requestParameters_policyDocument_Effect
            AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'list_accesskey_other_user',
            ruleComment : 'IAM사용자가 다른 사용자의 accesskey 조회',
            eventName: 'ListAccessKeys',
            eventSource: 'iam.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static',
            query:"MATCH (rule:Rule:Aws {
            ruleName : 'list_accesskey_other_user',
            ruleComment : 'IAM사용자가 다른 사용자의 accesskey 조회',
            eventName: 'ListAccessKeys',
            eventSource: 'iam.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND log.userIdentity_userName <> log.requestParameters_userName
            AND log.eventSource = rule.eventSource
            AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    '''
]
rule_detect_ec2 = [
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'open_database_port',
            ruleComment : '데이터베이스 서비스와 연결된 포트에서 aws security group을 전세계로 여는 경우 탐지',
            eventName : 'AuthorizeSecurityGroupIngress',
            portList : [1433, 3306, 5432, 5984, 6984, 6379, 9200, 27017],
            cidrIp : ['0.0.0.0/0', '::/0'],
            on_off : 1,
            eventSource: 'ec2.amazonaws.com',
            level: 3,
            ruleType : 'default',
            ruleClass : 'static',
            query:"MATCH (rule:Rule:Aws {
            ruleName : 'open_database_port',
            ruleComment : '데이터베이스 서비스와 연결된 포트에서 aws security group을 전세계로 여는 경우 탐지',
            eventName : 'AuthorizeSecurityGroupIngress',
            portList : [1433, 3306, 5432, 5984, 6984, 6379, 9200, 27017],
            cidrIp : ['0.0.0.0/0', '::/0'],
            on_off : 1,
            eventSource: 'ec2.amazonaws.com',
            level: 3,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND log.eventSource = rule.eventSource
            AND (ANY(key IN keys(log) WHERE key =~ 'responseElements_securityGroupRuleSet_items_\\d+_toPort' AND log[key] in rule.portList)
            OR ANY(key IN keys(log) WHERE key =~ 'responseElements_securityGroupRuleSet_items_\\d+_fromPort' AND log[key] in rule.portList))
            AND ANY(key IN keys(log) WHERE key =~ 'requestParameters_ipPermissions_items_\\d+_ipRanges_items_\\d+_cidrIp' AND log[key] in rule.cidrIp)	
        AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)
        "
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
            ruleType : 'default',
            ruleClass : 'static',
            query:"MATCH (rule:Rule:Aws {
            ruleName : 'security_group_permission_all',
            ruleComment : 'AuthorizeSecurityGroupIngress API를 사용하여 SECURITY GRUOP을 공개',
            eventName : 'AuthorizeSecurityGroupIngress',
            cidrIp : ['0.0.0.0/0', '::/0'],
            on_off : 1,
            eventSource: 'ec2.amazonaws.com',
            level: 3,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName = rule.eventName
        AND log.eventSource = rule.eventSource
        AND ANY(key IN keys(log) WHERE key =~ 'requestParameters_ipPermissions_items_\\d+_ipRanges_items_\\d+_cidrIp' AND log[key] in rule.cidrIp)
        AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
    })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'delete_vpc',
            ruleComment : 'EC2 VPC 삭제',
            eventName : 'DeleteVpc',
            on_off : 1,
            eventSource: 'ec2.amazonaws.com',
            level: 2,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'delete_vpc',
            ruleComment : 'EC2 VPC 삭제',
            eventName : 'DeleteVpc',
            on_off : 1,
            eventSource: 'ec2.amazonaws.com',
            level: 2,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName = rule.eventName
            AND log.eventSource = rule.eventSource
            AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'delete_subnet',
            ruleComment : 'EC2 서브넷 삭제',
            eventName : 'DeleteSubnet',
            on_off : 1,
            eventSource: 'ec2.amazonaws.com',
            level: 2,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'delete_subnet',
            ruleComment : 'EC2 서브넷 삭제',
            eventName : 'DeleteSubnet',
            on_off : 1,
            eventSource: 'ec2.amazonaws.com',
            level: 2,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName = rule.eventName
            AND log.eventSource = rule.eventSource
            AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
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
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'delete_ec2_log',
            ruleComment : 'ec2 로그 삭제 api가 호출될 경우',
            eventName : 'DeleteFlowLogs',
            eventSource: 'ec2.amazonaws.com',
            on_off : 1,
            level: 3,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName = rule.eventName
            AND log.eventSource = rule.eventSource
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'disable_ebs_encryption_default',
            ruleComment : 'default 유저에 의해 EBS 암호화가 풀렸을 때 경고',
            eventName : 'DisableEbsEncryptionByDefault',
            responseElements_DisableEbsEncryptionByDefaultResponse_ebsEncryptionByDefault : false,
            on_off : 1,
            eventSource: 'ec2.amazonaws.com',
            level: 2,
            ruleType : 'default',
            ruleClass : 'static',
            query:"MATCH (rule:Rule:Aws {
            ruleName : 'disable_ebs_encryption_default',
            ruleComment : 'default 유저에 의해 EBS 암호화가 풀렸을 때 경고',
            eventName : 'DisableEbsEncryptionByDefault',
            responseElements_DisableEbsEncryptionByDefaultResponse_ebsEncryptionByDefault : false,
            on_off : 1,
            eventSource: 'ec2.amazonaws.com',
            level: 2,
            ruleType : 'default',
            ruleClass : 'static'
            })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName = rule.eventName
        AND log.eventSource = rule.eventSource
        AND log.responseElements_DisableEbsEncryptionByDefaultResponse_ebsEncryptionByDefault = rule.responseElements_DisableEbsEncryptionByDefaultResponse_ebsEncryptionByDefault 
        AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'ebs_snapshot_public',
            ruleComment : 'ebs Snapshot이 공개로 설정되었을 경우',
            eventName : 'ModifySnapshotAttribute',
            requestParameters_createVolumePermission_add_items_group : 'all',
            requestParameters_attributeType : 'CREATE_VOLUME_PERMISSION',
            on_off : 1,
            eventSource: 'ec2.amazonaws.com',
            level: 2,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'ebs_snapshot_public',
            ruleComment : 'ebs Snapshot이 공개로 설정되었을 경우',
            eventName : 'ModifySnapshotAttribute',
            requestParameters_createVolumePermission_add_items_group : 'all',
            requestParameters_attributeType : 'CREATE_VOLUME_PERMISSION',
            on_off : 1,
            eventSource: 'ec2.amazonaws.com',
            level: 2,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName = rule.eventName
            AND ANY(key IN keys(log) WHERE key =~ 'requestParameters_createVolumePermission_add_items_\\d+_group' AND log[key] in rule.requestParameters_createVolumePermission_add_items_group )
            AND log.requestParameters_attributeType = rule.requestParameters_attributeType
            AND log.errorCode is null
            AND log.eventSource = rule.eventSource
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'ami_public',
            ruleComment : '생성한 AMI가 공개로 설정되었을 경우',
            eventName : 'ModifyImageAttribute',
            requestParameters_launchPermission_add_items_group : 'all',
            on_off : 1,
            eventSource: 'ec2.amazonaws.com',
            level: 2,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'ami_public',
            ruleComment : '생성한 AMI가 공개로 설정되었을 경우',
            eventName : 'ModifyImageAttribute',
            requestParameters_launchPermission_add_items_group : 'all',
            on_off : 1,
            eventSource: 'ec2.amazonaws.com',
            level: 2,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName = rule.eventName
            AND ANY(key IN keys(log) WHERE key =~ 'requestParameters_launchPermission_add_items_\\d+_group' AND log[key] in rule.requestParameters_launchPermission_add_items_group )
            AND log.eventSource = rule.eventSource
            AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'cli_import_ec2_keypair',
            ruleComment : 'cli를 통해 ec2 인스턴스에서 키 쌍 생성 후 퍼블릭 키 획득',
            eventName : 'ImportKeyPair',
            userAgent : 'cli',
            on_off : 1,
            eventSource: 'ec2.amazonaws.com',
            level: 3,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'cli_import_ec2_keypair',
            ruleComment : 'cli를 통해 ec2 인스턴스에서 키 쌍 생성 후 퍼블릭 키 획득',
            eventName : 'ImportKeyPair',
            userAgent : 'cli',
            on_off : 1,
            eventSource: 'ec2.amazonaws.com',
            level: 3,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND log.eventSource = rule.eventSource
        and toLower(log.userAgent) contains rule.userAgent
            AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
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
            level: 1,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'able_instance_api_termination',
            ruleComment : '콘솔, cli, api를 통해 인스턴스 종료할 수 있도록 변경',
            eventName : 'ModifyInstanceAttribute',
            requestParameters_disableApiTermination_value : false,
            on_off : 1,
            eventSource: 'ec2.amazonaws.com',
            level: 1,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND log.eventSource = rule.eventSource
            AND log.requestParameters_disableApiTermination_value = rule.requestParameters_disableApiTermination_value 
            AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
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
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'run_high_cpu_instance',
            ruleComment : 'aws 환경 내 인스턴스보다 과도하게 높은 성능의 cpu ec2 인스턴스 생성 행위',
            eventName : 'RunInstances',
            requestParameters_instanceType : 10,
            on_off : 1,
            eventSource: 'ec2.amazonaws.com',
            level: 2,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WITH split(log.requestParameters_instanceType, '.')[1] as instanceType, rule, log
        WHERE log.eventName CONTAINS rule.eventName
            AND log.eventSource = rule.eventSource
            AND toInteger(apoc.text.regexGroups(instanceType, \\\"(\\d+)\\\")[0][0]) >= rule.requestParameters_instanceType 
            AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'iam_network_acl_all_allow',
            ruleComment : 'iam사용자가 모든 트래픽을 허용하는 네트워크 접근제어 리스트 규칙 생성',
            eventName : 'CreateNetworkAclEntry',
            requestParameters_ruleAction : 'allow',
            requestParameters_aclProtocol : '-1',
            requestParameters_cidrBlock : '0.0.0.0/0',
            requestParameters_ipv6CidrBlock : '::/0',
            requestParameters_portRange_to : 0,
            requestParameters_portRange_from : 0,
            eventSource: 'ec2.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'iam_network_acl_all_allow',
            ruleComment : 'iam사용자가 모든 트래픽을 허용하는 네트워크 접근제어 리스트 규칙 생성',
            eventName : 'CreateNetworkAclEntry',
            requestParameters_ruleAction : 'allow',
            requestParameters_aclProtocol : '-1',
            requestParameters_cidrBlock : '0.0.0.0/0',
            requestParameters_ipv6CidrBlock : '::/0',
            requestParameters_portRange_to : 0,
            requestParameters_portRange_from : 0,
            eventSource: 'ec2.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND log.eventSource = rule.eventSource
            AND log.requestParameters_ruleAction = rule.requestParameters_ruleAction
            AND ((log.requestParameters_cidrBlock = rule.requestParameters_cidrBlock
            OR log.requestParameters_ipv6CidrBlock = rule.requestParameters_ipv6CidrBlock)
            OR log.requestParameters_aclProtocol = rule.requestParameters_aclProtocol
            OR (log.requestParameters_portRange_to = rule.requestParameters_portRange_to 
            OR log.requestParameters_portRange_from = rule.requestParameters_portRange_from))
            AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'network_gateway_api_call',
            ruleComment : '네트워크 게이트웨이 생성/수정/삭제 행위',
            eventName : ['CreateCustomerGateway', 'DeleteCustomerGateway', 'AttachInternetGateway', 'CreateInternetGateway', 'DeleteInternetGateway', 'DetachInternetGateway'],
            on_off : 1,
            eventSource: 'ec2.amazonaws.com',
            level: 2,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'network_gateway_api_call',
            ruleComment : '네트워크 게이트웨이 생성/수정/삭제 행위',
            eventName : ['CreateCustomerGateway', 'DeleteCustomerGateway', 'AttachInternetGateway', 'CreateInternetGateway', 'DeleteInternetGateway', 'DetachInternetGateway'],
            on_off : 1,
            eventSource: 'ec2.amazonaws.com',
            level: 2,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName in rule.eventName
            AND log.eventSource = rule.eventSource
            AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    '''
]
rule_detect_s3 = [
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 's3_mfa_delete',
            ruleComment : 'Aws 저장소 서비스인 S3 관련 작업을 할 때 MFA를 요구하도록 하는 정책 비활성화 이벤트 발생',
            eventName : 'PutBucketVersioning',
            requestParameters_VersioningConfiguration_MfaDelete : 'Enabled',
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 's3_mfa_delete',
            ruleComment : 'Aws 저장소 서비스인 S3 관련 작업을 할 때 MFA를 요구하도록 하는 정책 비활성화 이벤트 발생',
            eventName : 'PutBucketVersioning',
            requestParameters_VersioningConfiguration_MfaDelete : 'Enabled',
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND log.eventSource = rule.eventSource
            AND log.requestParameters_VersioningConfiguration_MfaDelete = rule.requestParameters_VersioningConfiguration_MfaDelete 
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
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
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'ec2_list_buckets',
            ruleComment : 'ec2 인스턴스로부터 s3 버킷 목록 조회 요청 이벤트 발생',
            eventName : 'ListBuckets',
            userIdentity_type : 'AssumedRole',
            userIdentity_principalId : 'i-',
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND log.userIdentity_type = rule.userIdentity_type 
            AND log.userIdentity_principalId CONTAINS rule.userIdentity_principalId 
            AND log.eventSource = rule.eventSource
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'delete_bucket_cloudtrail',
            ruleComment : 'cloudtrail 로그 관련 s3 버킷 삭제',
            eventName : 'DeleteBucket',
            requestParameters_bucketName : 'cloudtrail',
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 3,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'delete_bucket_cloudtrail',
            ruleComment : 'cloudtrail 로그 관련 s3 버킷 삭제',
            eventName : 'DeleteBucket',
            requestParameters_bucketName : 'cloudtrail',
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 3,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND log.requestParameters_bucketName CONTAINS rule.requestParameters_bucketName 
            AND log.eventSource = rule.eventSource
            AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'put_bucket_public_access',
            ruleComment : 's3 버킷에 대한 퍼블릭 액세스 허용',
            eventName : 'PutBucketPublicAccessBlock',
            publicAccessBlockConfiguration : FALSE,
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'put_bucket_public_access',
            ruleComment : 's3 버킷에 대한 퍼블릭 액세스 허용',
            eventName : 'PutBucketPublicAccessBlock',
            publicAccessBlockConfiguration : FALSE,
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND log.eventSource = rule.eventSource
            AND (log.requestParameters_PublicAccessBlockConfiguration_BlockPublicPolicy = rule.publicAccessBlockConfiguration 
                        OR log.requestParameters_PublicAccessBlockConfiguration_BlockPublicAcls = rule.publicAccessBlockConfiguration 
                        OR log.requestParameters_PublicAccessBlockConfiguration_RestrictPublicBuckets = rule.publicAccessBlockConfiguration
                        OR log.requestParameters_PublicAccessBlockConfiguration_IgnorePublicAcls = rule.publicAccessBlockConfiguration)
            AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
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
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'disable_s3_logging',
            ruleComment : '버킷에 대한 s3 서버 액세스 로깅 비활성화',
            eventName : 'PutBucketLogging',
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 1,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND log.LoggingEnabled is null
            AND log.eventSource = rule.eventSource
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'iam_allow_s3_global_allUsers',
            ruleComment : 'iam사용자가 버킷 액세스 정책 변경을 통해 모든 aws 사용자에게 s3 버킷에 대한 퍼블릭 액세스 권한 부여',
            eventName : 'PutBucketAcl',
            userIdentity_type : 'IAMUser',
            accessControlList : 'AllUsers',
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'iam_allow_s3_global_allUsers',
            ruleComment : 'iam사용자가 버킷 액세스 정책 변경을 통해 모든 aws 사용자에게 s3 버킷에 대한 퍼블릭 액세스 권한 부여',
            eventName : 'PutBucketAcl',
            userIdentity_type : 'IAMUser',
            accessControlList : 'AllUsers',
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND log.userIdentity_type = rule.userIdentity_type
        AND log.eventSource = rule.eventSource
            AND log.errorCode is null
        unwind [key IN keys(log) WHERE key =~ 'requestParameters_AccessControlPolicy_AccessControlList_Grant_\\d+_Grantee_URI'] as k
        with k, log, rule
        where log[k] contains rule.accessControlList
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'delete_bucket_life_cycle',
            ruleComment : 's3 버킷에 할당된 수명 주기 정책 삭제 요청 이벤트 발생',
            eventName : 'DeleteBucketLifecycle',
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 1,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'delete_bucket_life_cycle',
            ruleComment : 's3 버킷에 할당된 수명 주기 정책 삭제 요청 이벤트 발생',
            eventName : 'DeleteBucketLifecycle',
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 1,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND log.eventSource = rule.eventSource
            AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'create_s3_public_access_point',
            ruleComment : 's3 버킷에 대한 퍼블릭 액세스 포인트 생성',
            eventName : 'CreateAccessPoint',
            publicAccessBlockConfiguration : false,
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'create_s3_public_access_point',
            ruleComment : 's3 버킷에 대한 퍼블릭 액세스 포인트 생성',
            eventName : 'CreateAccessPoint',
            publicAccessBlockConfiguration : false,
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND (log.requestParameters_CreateAccessPointRequest_PublicAccessBlockConfiguration_BlockPublicPolicy = rule.publicAccessBlockConfiguration 
                        OR log.requestParameters_CreateAccessPointRequest_PublicAccessBlockConfiguration_BlockPublicAcls = rule.publicAccessBlockConfiguration 
                        OR log.requestParameters_CreateAccessPointRequest_PublicAccessBlockConfiguration_RestrictPublicBuckets= rule.publicAccessBlockConfiguration
                        OR log.requestParameters_CreateAccessPointRequest_PublicAccessBlockConfiguration_IgnorePublicAcls = rule.publicAccessBlockConfiguration)
            AND log.eventSource = rule.eventSource
            AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
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
            level: 2,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 's3_bucketAcl_public',
            ruleComment : 's3 Bucket Acl Storage를 public으로 변경하는 경우',
            eventName : 'PutBucketAcl',
            `requestParameters_x-amz-acl` : 'public',
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND log.`requestParameters_x-amz-acl` CONTAINS rule.`requestParameters_x-amz-acl`
            AND log.eventSource = rule.eventSource
            AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'bucket_replication',
            ruleComment : 's3 버킷에 대한 복제구성 생성',
            eventName : 'PutBucketReplication',
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 3,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'bucket_replication',
            ruleComment : 's3 버킷에 대한 복제구성 생성',
            eventName : 'PutBucketReplication',
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 3,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND log.eventSource = rule.eventSource
            AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'delete_bucket_encryption',
            ruleComment : 's3 버킷 암호화 해제 행위',
            eventName : 'DeleteBucketEncryption',
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'delete_bucket_encryption',
            ruleComment : 's3 버킷 암호화 해제 행위',
            eventName : 'DeleteBucketEncryption',
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND log.eventSource = rule.eventSource
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'all_action_bucket_access_point',
            ruleComment : 's3 버킷 액세스 포인트에 s3에 대한 모든 행위 허용 정책 설정',
            eventName : 'PutAccessPointPolicy',
            requestParameters_AccessPointPolicy_Action : '"Action": "s3:*"',
            requestParameters_AccessPointPolicy_Effect : '"Effect": "Allow"',
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'all_action_bucket_access_point',
            ruleComment : 's3 버킷 액세스 포인트에 s3에 대한 모든 행위 허용 정책 설정',
            eventName : 'PutAccessPointPolicy',
            requestParameters_AccessPointPolicy_Action : '\\\"Action\\\": \\\"s3:*\\\"',
            requestParameters_AccessPointPolicy_Effect : '\\\"Effect\\\":\\\"Allow\\\"',
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName = rule.eventName
        and log.eventSource = rule.eventSource
        and log.requestParameters_PutAccessPointPolicyRequest_Policy contains rule.requestParameters_AccessPointPolicy_Action
        and log.requestParameters_PutAccessPointPolicyRequest_Policy contains rule.requestParameters_AccessPointPolicy_Effect
            AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'bucket_life_cycle_disabled',
            ruleComment : 'Aws 저장소 서비스인 S3 버킷에 할당된 수명 주기 정책 비활성화 요청 이벤트 발생',
            eventName : 'PutBucketLifecycle',
            requestParameters_LifecycleConfiguration_Rule_Status : 'Disabled',
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 1,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH  (rule:Rule:Aws {
            ruleName : 'bucket_life_cycle_disabled',
            ruleComment : 'Aws 저장소 서비스인 S3 버킷에 할당된 수명 주기 정책 비활성화 요청 이벤트 발생',
            eventName : 'PutBucketLifecycle',
            requestParameters_LifecycleConfiguration_Rule_Status : 'Disabled',
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 1,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND log.eventSource = rule.eventSource
            AND log.requestParameters_LifecycleConfiguration_Rule_Status = rule.requestParameters_LifecycleConfiguration_Rule_Status
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'bucket_expiration_90',
            ruleComment : 'Aws 저장소 서비스인 S3 버킷에 할당된 수명 주기 정책에서 만료 기간이 90일 이내 설정 요청 이벤트 발생',
            eventName : 'PutBucketLifecycle',
            requestParameters_LifecycleConfiguration_Rule_Expiration_Days : 90,
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 1,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'bucket_expiration_90',
            ruleComment : 'Aws 저장소 서비스인 S3 버킷에 할당된 수명 주기 정책에서 만료 기간이 90일 이내 설정 요청 이벤트 발생',
            eventName : 'PutBucketLifecycle',
            requestParameters_LifecycleConfiguration_Rule_Expiration_Days : 90,
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 1,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND log.eventSource = rule.eventSource
            AND log.requestParameters_LifecycleConfiguration_Rule_Expiration_Days < rule.requestParameters_LifecycleConfiguration_Rule_Expiration_Days 
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 's3_policy_api',
            ruleComment : 'S3의 정책이 API를 통해 변경',
            eventName : 'PutBucketPolicy',
            eventType : 'AwsApiCall',
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 1,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 's3_policy_api',
            ruleComment : 'S3의 정책이 API를 통해 변경',
            eventName : 'PutBucketPolicy',
            eventType : 'AwsApiCall',
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 1,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND log.eventSource = rule.eventSource
            AND log.eventType = rule.eventType 
            AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'delete_s3_bucket',
            ruleComment : 'S3 버킷 삭제',
            eventName : 'DeleteBucket',
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'delete_s3_bucket',
            ruleComment : 'S3 버킷 삭제',
            eventName : 'DeleteBucket',
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
        AND log.eventSource = rule.eventSource
        AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'delete_s3_bucket_policy',
            ruleComment : 'S3 버킷 규칙 삭제',
            eventName : 'DeleteBucketPolicy',
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'delete_s3_bucket_policy',
            ruleComment : 'S3 버킷 규칙 삭제',
            eventName : 'DeleteBucketPolicy',
            eventSource: 's3.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND log.eventSource = rule.eventSource
            AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    '''
]    
rule_detect_cloudTrail = [
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'delete_trail',
            ruleComment : 'cloudtrail 로그 기록 삭제',
            eventName : 'DeleteTrail',
            eventSource: 'cloudtrail.amazonaws.com',
            on_off : 1,
            level: 3,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'delete_trail',
            ruleComment : 'cloudtrail 로그 기록 삭제',
            eventName : 'DeleteTrail',
            eventSource: 'cloudtrail.amazonaws.com',
            on_off : 1,
            level: 3,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND log.eventSource = rule.eventSource
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
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
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'stop_logging',
            ruleComment : 'cloudtrail 로그 기록 중단',
            eventName : 'StopLogging',
            eventSource: 'cloudtrail.amazonaws.com',
            on_off : 1,
            level: 3,
            ruleType : 'default',
            ruleClass : 'static'
            
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND log.eventSource = rule.eventSource
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)
        "
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'create_trail_event_selector',
            ruleComment : 'Aws 로그 서비스인 CloudTrail에서 이벤트 필터링을 담당하는 event selector 생성 이벤트 발생',
            eventName : 'PutEventSelectors',
            eventSource: 'cloudtrail.amazonaws.com',
            on_off : 1,
            level: 1,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'create_trail_event_selector',
            ruleComment : 'Aws 로그 서비스인 CloudTrail에서 이벤트 필터링을 담당하는 event selector 생성 이벤트 발생',
            eventName : 'PutEventSelectors',
            eventSource: 'cloudtrail.amazonaws.com',
            on_off : 1,
            level: 1,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND log.eventSource = rule.eventSource
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'update_trail',
            ruleComment : 'Aws 로그 서비스인 CloudTrail의 설정 변경 이벤트 발생',
            eventName : 'UpdateTrail',
            eventSource: 'cloudtrail.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'update_trail',
            ruleComment : 'Aws 로그 서비스인 CloudTrail의 설정 변경 이벤트 발생',
            eventName : 'UpdateTrail',
            eventSource: 'cloudtrail.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND log.eventSource = rule.eventSource
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'eventdatastore_termination_protection_disabled',
            ruleComment : 'cloudtrail 이벤트 데이터 저장소 삭제 방지 기능 해제',
            eventName : 'UpdateEventDataStore',
            requestParameters_eventDataStore : 'cloudtrail',
            requestParameters_terminationProtectionEnabled : false,
            eventSource: 'cloudtrail.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'eventdatastore_termination_protection_disabled',
            ruleComment : 'cloudtrail 이벤트 데이터 저장소 삭제 방지 기능 해제',
            eventName : 'UpdateEventDataStore',
            requestParameters_eventDataStore : 'cloudtrail',
            requestParameters_terminationProtectionEnabled : false,
            eventSource: 'cloudtrail.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND log.requestParameters_eventDataStore contains rule.requestParameters_eventDataStore 
            AND log.requestParameters_terminationProtectionEnabled = rule.requestParameters_terminationProtectionEnabled 
            AND log.eventSource = rule.eventSource
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    '''
]   
rule_detect_rds = [
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'rds_snapshot_public',
            ruleComment : 'rds 스냅샷이 공개로 변경',
            eventName : ['ModifyDBClusterSnapshotAttribute', 'ModifyDBSnapshotAttribute'],
            requestParameters_valuesToAdd : 'all',
            eventSource: 'rds.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'rds_snapshot_public',
            ruleComment : 'rds 스냅샷이 공개로 변경',
            eventName : ['ModifyDBClusterSnapshotAttribute', 'ModifyDBSnapshotAttribute'],
            requestParameters_valuesToAdd : 'all',
            eventSource: 'rds.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName in rule.eventName 
            AND ANY(key IN keys(log) WHERE key =~ 'requestParameters_valuesToAdd_\\d' AND log[key]  = rule.requestParameters_valuesToAdd)
            AND log.eventSource = rule.eventSource
            AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'promote_read_replica',
            ruleComment : '읽기 전용 복제본 db 클러스터를 독립 실행형 db 클러스터로 승격',
            eventName : ['PromoteReadReplicaDBCluster','PromoteReadReplica'],
            eventSource: 'rds.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'promote_read_replica',
            ruleComment : '읽기 전용 복제본 db 클러스터를 독립 실행형 db 클러스터로 승격',
            eventName : ['PromoteReadReplicaDBCluster','PromoteReadReplica'],
            eventSource: 'rds.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName in rule.eventName
            AND log.eventSource = rule.eventSource
            AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
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
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'db_public_access',
            ruleComment : 'DB 인스턴스에 공개적으로 접근 가능하도록 수정',
            eventName : 'ModifyDBInstance',
            responseElements_publiclyAccessible : true,
            eventSource: 'rds.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND log.responseElements_publiclyAccessible = rule.responseElements_publiclyAccessible
            AND log.eventSource = rule.eventSource
            AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'restore_db_instance_from_snapshot_error',
            ruleComment : '권한 없는 사용자의 볼륨 스냅샷에서 전체 db 인스턴스 백업 시도 실패',
            eventName : 'RestoreDBInstanceFromDBSnapshot',
            errorCode : 'AccessDenied',
            eventSource: 'rds.amazonaws.com',
            on_off : 1,
            level: 1,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'restore_db_instance_from_snapshot_error',
            ruleComment : '권한 없는 사용자의 볼륨 스냅샷에서 전체 db 인스턴스 백업 시도 실패',
            eventName : 'RestoreDBInstanceFromDBSnapshot',
            errorCode : 'AccessDenied',
            eventSource: 'rds.amazonaws.com',
            on_off : 1,
            level: 1,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND log.errorCode = rule.errorCode 
            AND log.eventSource = rule.eventSource
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'restore_db_instance_from_snapshot_public',
            ruleComment : '스냅샷에서 db 인스턴스 퍼블릭 액세스 허용하도록 백업',
            eventName : 'RestoreDBInstanceFromDBSnapshot',
            requestParameters_publiclyAccessible : true,
            eventSource: 'rds.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'restore_db_instance_from_snapshot_public',
            ruleComment : '스냅샷에서 db 인스턴스 퍼블릭 액세스 허용하도록 백업',
            eventName : 'RestoreDBInstanceFromDBSnapshot',
            requestParameters_publiclyAccessible : true,
            eventSource: 'rds.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND log.requestParameters_publiclyAccessible = rule.requestParameters_publiclyAccessible 
            AND log.eventSource = rule.eventSource
            AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
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
            level: 1,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'rds_delete_protect_disable',
            ruleComment : 'RDS 인스턴스 삭제 방지 기능 해제',
            eventName : ['ModifyDBCluster', 'ModifyDBInstance'],
            responseElements_deletionProtection : false,
            eventSource: 'rds.amazonaws.com',
            on_off : 1,
            level: 1,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName in rule.eventName 
            AND log.responseElements_deletionProtection = rule.responseElements_deletionProtection 
            AND log.eventSource = rule.eventSource
            AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
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
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'delete_db_cluster',
            ruleComment : 'IAM 사용자가 RDS DB 클러스터 또는 인스턴스 삭제',
            eventName : ['DeleteDBCluster', 'DeleteDBInstance'],
            userIdentity_type : 'IAMUser',
            eventSource: 'rds.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName in rule.eventName 
            AND log.userIdentity_type = rule.userIdentity_type 
            AND log.eventSource = rule.eventSource
            AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'stop_rds_db',
            ruleComment : 'RDS 내 DB 클러스터 / 인스턴스 중지',
            eventName : ['StopDBInstance', 'StopDBCluster'],
            eventSource: 'rds.amazonaws.com',
            on_off : 1,
            level: 1,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'stop_rds_db',
            ruleComment : 'RDS 내 DB 클러스터 / 인스턴스 중지',
            eventName : ['StopDBInstance', 'StopDBCluster'],
            eventSource: 'rds.amazonaws.com',
            on_off : 1,
            level: 1,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName in rule.eventName
            AND log.eventSource = rule.eventSource
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    '''
]
rule_detect_ecs = [
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'create_fargate_curl_task_definition',
            ruleComment : '다른 주소로 연결되는 command를 호함해 컨테이너 자동시작 task definition 생성',
            eventName: 'RegisterTaskDefinition',
            requestParameters_containerDefinitions_command : 'curl',
            requestParameters_requiresCompatibilities  : 'FARGATE',
            eventSource : 'ecs.amazonaws.com',
            level : 3,
            ruleType : 'default',
            ruleClass : 'static',
            on_off : 1,
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'create_fargate_curl_task_definition',
            ruleComment : '다른 주소로 연결되는 command를 호함해 컨테이너 자동시작 task definition 생성',
            eventName: 'RegisterTaskDefinition',
            requestParameters_containerDefinitions_command : 'curl',
            requestParameters_requiresCompatibilities  : 'FARGATE',
            eventSource : 'ecs.amazonaws.com',
            level : 3,
            ruleType : 'default',
            ruleClass : 'static',
            on_off : 1
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND ANY(key IN keys(log) WHERE key =~ 'requestParameters_containerDefinitions_\\d+_command_\\d' AND log[key] contains rule.requestParameters_containerDefinitions_command )
            AND ANY(key IN keys(log) WHERE key =~ 'requestParameters_requiresCompatibilities_\\d' AND log[key] = rule.requestParameters_requiresCompatibilities)
            AND log.eventSource = rule.eventSource
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'delete_ecs_cluster',
            ruleComment : 'ECS 클러스터가 삭제된 경우',
            eventName: 'DeleteCluster',
            eventSource : 'ecs.amazonaws.com',
            level : 2,
            ruleType : 'default',
            ruleClass : 'static',
            on_off : 1,
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'delete_ecs_cluster',
            ruleComment : 'ECS 클러스터가 삭제된 경우',
            eventName: 'DeleteCluster',
            eventSource : 'ecs.amazonaws.com',
            level : 2,
            ruleType : 'default',
            ruleClass : 'static',
            on_off : 1
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            AND log.eventSource = rule.eventSource
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    '''
]
rule_detect_cloudWatch = [
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'disable_alarm_actions',
            ruleComment : 'cloudwatch 경보 삭제',
            eventName: ['DeleteAlarms', 'DisableAlarmActions'],
            on_off : 1,
            ruleType : 'default',
            ruleClass : 'static',
            eventSource : 'monitoring.amazonaws.com',
            level : 3,
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'disable_alarm_actions',
            ruleComment : 'cloudwatch 경보 삭제',
            eventName: ['DeleteAlarms', 'DisableAlarmActions'],
            on_off : 1,
            ruleType : 'default',
            ruleClass : 'static',
            eventSource : 'monitoring.amazonaws.com',
            level : 3
            })
            WITH rule
            MATCH (log:Log:Aws)
            WHERE log.eventName in rule.eventName
            AND log.eventSource = rule.eventSource
            WITH rule, log
            MERGE (log)-[:DETECTED]->(rule)
            "
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName in rule.eventName
        AND log.eventSource = rule.eventSource
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'delete_log_group',
            ruleComment : 'cloudwatch 모니터링 대상 그룹 삭제 이벤트 발생',
            eventName: 'DeleteLogGroup',
            on_off : 1,
            eventSource : 'logs.amazonaws.com',
            ruleType : 'default',
            ruleClass : 'static',
            level : 3,
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'delete_log_group',
            ruleComment : 'cloudwatch 모니터링 대상 그룹 삭제 이벤트 발생',
            eventName: 'DeleteLogGroup',
            on_off : 1,
            eventSource : 'logs.amazonaws.com',
            ruleType : 'default',
            ruleClass : 'static',
            level : 3
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName = rule.eventName
            AND log.eventSource = rule.eventSource
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'delete_disable_cloudwatch_rule',
            ruleComment : 'cloudwatch 모니터링 룰을 비활성화 또는 삭제하는 이벤트 발생',
            eventName: ['DisableRule','DeleteRule'],
            on_off : 1,
            eventSource : 'events.amazonaws.com',
            ruleType : 'default',
            ruleClass : 'static',
            level : 3,
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'delete_disable_cloudwatch_rule',
            ruleComment : 'cloudwatch 모니터링 룰을 비활성화 또는 삭제하는 이벤트 발생',
            eventName: ['DisableRule','DeleteRule'],
            on_off : 1,
            eventSource : 'events.amazonaws.com',
            ruleType : 'default',
            ruleClass : 'static',
            level : 3
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName in rule.eventName
            AND log.eventSource = rule.eventSource
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    '''
]    
rule_detect_signin = [
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'aws_account_assume_role',
            ruleComment : '외부 aws 계정으로부터 역할 변경 이벤트 발생',
            eventName: 'SwitchRole',
            userIdentity_type : 'AssumedRole',
            userIdentity_accountId : '622751588873',
            eventSource: 'signin.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
            ruleName : 'aws_account_assume_role',
            ruleComment : '외부 aws 계정으로부터 역할 변경 이벤트 발생',
            eventName: 'SwitchRole',
            userIdentity_type : 'AssumedRole',
            userIdentity_accountId : '622751588873',
            eventSource: 'signin.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName CONTAINS rule.eventName
            and log.userIdentity_type = rule.userIdentity_type
            and log.eventSource = rule.eventSource
            and split(log.additionalEventData_SwitchFrom, ':')[4] <> rule.userIdentity_accountId
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    '''
]
rule_detect_cognito = [
    '''
        MERGE (rule:Rule:Aws {
        ruleName : 'unknown_access',
        ruleComment : 'unknown 사용자가 aws 환경에 접근',
        userIdentity_type : 'Unknown',
        eventSource: 'cognito-idp.amazonaws.com',
        on_off : 1,
        level: 1,
        ruleType : 'default',
        ruleClass : 'static',
        query: "MATCH (rule:Rule:Aws {
        ruleName : 'unknown_access',
        ruleComment : 'unknown 사용자가 aws 환경에 접근',
        userIdentity_type : 'Unknown',
        eventSource: 'cognito-idp.amazonaws.com',
        on_off : 1,
        level: 1,
        ruleType : 'default',
        ruleClass : 'static'
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.userIdentity_type CONTAINS rule.userIdentity_type 
        AND log.eventSource = rule.eventSource
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    '''
]
rule_detect_kms = [
    '''
        MERGE (rule:Rule:Aws {
        ruleName : 'schedule_kms_key_deletion',
        ruleComment : 'key가 비정상적인 삭제 예약 설정된 경우',
        eventName: 'ScheduleKeyDeletion',
        on_off : 1,
        ruleType : 'default',
        ruleClass : 'static',
        eventSource : 'kms.amazonaws.com',
        level : 2,
        query: "MATCH (rule:Rule:Aws {
        ruleName : 'schedule_kms_key_deletion',
        ruleComment : 'key가 비정상적인 삭제 예약 설정된 경우',
        eventName: 'ScheduleKeyDeletion',
        on_off : 1,
        ruleType : 'default',
        ruleClass : 'static',
        eventSource : 'kms.amazonaws.com',
        level : 2
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName in rule.eventName
        AND log.eventSource = rule.eventSource
        AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
        ruleName : 'disable_kms_key',
        ruleComment : 'key가 비정상적인 방식으로 비활성화 된 경우',
        eventName: 'DisableKey',
        on_off : 1,
        ruleType : 'default',
        ruleClass : 'static',
        eventSource : 'kms.amazonaws.com',
        level : 2,
        query: "MATCH (rule:Rule:Aws {
        ruleName : 'disable_kms_key',
        ruleComment : 'key가 비정상적인 방식으로 비활성화 된 경우',
        eventName: 'DisableKey',
        on_off : 1,
        ruleType : 'default',
        ruleClass : 'static',
        eventSource : 'kms.amazonaws.com',
        level : 2
        })
        WITH rule
        MATCH (log:Log:Aws)
        WHERE log.eventName in rule.eventName
        AND log.eventSource = rule.eventSource
        AND log.errorCode is null
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)"
        })
    '''
]
rule_detect_secretsManager = [
    '''
        MERGE (rule:Rule:Aws {
        ruleName : 'get_secret_value',
        ruleComment : 'secret value 획득',
        eventName : 'GetSecretValue',
        eventSource: 'secretsmanager.amazonaws.com',
        on_off : 1,
        level: 3,
        ruleType : 'default',
        ruleClass : 'static',
        query: "MATCH (rule:Rule:Aws {
                        ruleName : 'get_secret_value',
                        ruleComment : 'secret value 획득',
                        eventName : 'GetSecretValue',
                        eventSource: 'secretsmanager.amazonaws.com',
                        on_off : 1,
                        level: 3,
                        ruleType : 'default',
                        ruleClass : 'static'
                    })
                    WITH rule
                    MATCH (log:Log:Aws)
                    WHERE log.eventName CONTAINS rule.eventName 
                        AND log.eventSource = rule.eventSource
                    WITH rule, log
                    MERGE (log)-[:DETECTED]->(rule)"
        })
    '''
]
rule_detect_gaurdDuty = [
    '''
        MERGE (rule:Rule:Aws {
        ruleName : 'delete_publishing_dst',
        ruleComment : 'GuardDuty 탐지 및 알림 대상 삭제',
        eventName : 'DeletePublishingDestination',
        eventSource: 'guardduty.amazonaws.com',
        on_off : 1,
        level: 3,
        ruleType : 'default',
        ruleClass : 'static',
        query: "MATCH (rule:Rule:Aws {
                ruleName : 'delete_publishing_dst',
                ruleComment : 'GuardDuty 탐지 및 알림 대상 삭제',
                eventName : 'DeletePublishingDestination',
                eventSource: 'guardduty.amazonaws.com',
                on_off : 1,
                level: 3,
                ruleType : 'default',
                ruleClass : 'static'
            })
            WITH rule
            MATCH (log:Log:Aws)
            WHERE log.eventName CONTAINS rule.eventName 
                AND log.eventSource = rule.eventSource
            WITH rule, log
            MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
        ruleName : 'delete_detector',
        ruleComment : 'GuardDuty 탐지기 제거',
        eventName : 'DeleteDetector',
        eventSource: 'guardduty.amazonaws.com',
        on_off : 1,
        level: 3,
        ruleType : 'default',
        ruleClass : 'static',
        query: "MATCH (rule:Rule:Aws {
                        ruleName : 'delete_detector',
                        ruleComment : 'GuardDuty 탐지기 제거',
                        eventName : 'DeleteDetector',
                        eventSource: 'guardduty.amazonaws.com',
                        on_off : 1,
                        level: 3,
                        ruleType : 'default',
                        ruleClass : 'static'
                    })
                    WITH rule
                    MATCH (log:Log:Aws)
                    WHERE log.eventName CONTAINS rule.eventName 
                        AND log.eventSource = rule.eventSource
                    WITH rule, log
                    MERGE (log)-[:DETECTED]->(rule)"
        })
    ''',
    '''
        MERGE (rule:Rule:Aws {
        ruleName : 'delete_threat_intel_set',
        ruleComment : 'GuardDuty 내 위협 삭제 API호출',
        eventName : 'DeleteThreatIntelSet',
        eventSource: 'guardduty.amazonaws.com',
        on_off : 1,
        level: 3,
        ruleType : 'default',
        ruleClass : 'static',
        query: "MATCH (rule:Rule:Aws {
                        ruleName : 'delete_threat_intel_set',
                        ruleComment : 'GuardDuty 내 위협 삭제 API호출',
                        eventName : 'DeleteThreatIntelSet',
                        eventSource: 'guardduty.amazonaws.com',
                        on_off : 1,
                        level: 3,
                        ruleType : 'default',
                        ruleClass : 'static'
                    })
                    WITH rule
                    MATCH (log:Log:Aws)
                    WHERE log.eventName CONTAINS rule.eventName 
                        AND log.eventSource = rule.eventSource
                    WITH rule, log
                    MERGE (log)-[:DETECTED]->(rule)"
        })
    '''
]
rule_detect_waf = [
    '''
        MERGE (rule:Rule:Aws {
            ruleName : 'update_web_acl_rules',
            ruleComment : 'WAF 웹 접근통제 리스트에서 규칙 삭제',
            eventName : 'UpdateWebACL',
            eventSource: 'wafv2.amazonaws.com',
            on_off : 1,
            level: 2,
            ruleType : 'default',
            ruleClass : 'static',
            query: "MATCH (rule:Rule:Aws {
                    ruleName : 'update_web_acl_rules',
                    ruleComment : 'WAF 웹 접근통제 리스트에서 규칙 삭제',
                    eventName : 'UpdateWebACL',
                    eventSource: 'wafv2.amazonaws.com',
                    on_off : 1,
                    level: 2,
                    ruleType : 'default',
                    ruleClass : 'static'
                })
                WITH rule
                MATCH (log:Log:Aws)
                WHERE log.eventName CONTAINS rule.eventName 
                    AND log.eventSource = rule.eventSource
                    AND log.requestParameters_rules is null
                WITH rule, log
                MERGE (log)-[:DETECTED]->(rule)"
        })
    '''
]

rule_detect_query = []
merge_query_list = ['rule_detect_all',
                   'rule_detect_iam',
                   'rule_detect_ec2',
                   'rule_detect_s3',
                   'rule_detect_cloudTrail',
                   'rule_detect_rds',
                   'rule_detect_ecs',
                   'rule_detect_cloudWatch',
                   'rule_detect_signin',
                   'rule_detect_cognito',
                   'rule_detect_kms',
                   'rule_detect_secretsManager',
                   'rule_detect_gaurdDuty',
                   'rule_detect_waf'
                   ]
for query_name in merge_query_list:
    current_list = globals().get(query_name)
    rule_detect_query.extend(current_list)
    
queries_per_thread = len(rule_detect_query) // 5
for i in range(5):
    start = i * queries_per_thread
    end = (i + 1) * queries_per_thread if i < 5 - 1 else len(rule_detect_query)
    thread_queries = rule_detect_query[start:end]