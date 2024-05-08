flow_default = [
'''
    MERGE (flow1:Flow:Aws {
        flowName : 'respond_auth_challenge',
        flowComment : '사용자 유효성 검사 성공',
        eventName : 'RespondToAuthChallenge'
    })
    MERGE (flow2:Flow:Aws {
        flowName : 'get_user_cli_with_access_token',
        flowComment : 'accessToken을 획득해 aws-cli 상에서 사용자 조회',
        eventName : 'GetUser',
        userAgent : 'aws-cli',
        eventSource : 'cognito-idp.amazonaws.com'
    })
    MERGE (rule:Rule:Aws {
        ruleName : 'check_policy_with_cognito_token',
        ruleComment : 'aws Cognito 사용자 디렉터리에서 로그인 시 획득한 accessToken을 통해 사용자 권한 확인',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        on_off : 1,
        level: 2,
        ruleType: 'default',
        ruleClass : 'dynamic',
        query: "MATCH (flow1:Flow:Aws {
        flowName : 'respond_auth_challenge',
        flowComment : '사용자 유효성 검사 성공',
        eventName : 'RespondToAuthChallenge'
    })
    MATCH (flow2:Flow:Aws {
        flowName : 'get_user_cli_with_access_token',
        flowComment : 'accessToken을 획득해 aws-cli 상에서 사용자 조회',
        eventName : 'GetUser',
        userAgent : 'aws-cli',
        eventSource : 'cognito-idp.amazonaws.com'
    })
    MATCH (rule:Rule:Aws {
        ruleName : 'check_policy_with_cognito_token',
        ruleComment : 'aws Cognito 사용자 디렉터리에서 로그인 시 획득한 accessToken을 통해 사용자 권한 확인',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        on_off : 1,
        level: 2,
        ruleType: 'default',
        ruleClass : 'dynamic'
    })
    WITH flow1, flow2, rule
    MATCH (log1:Log:Aws{eventName:flow1.eventName}), (log2:Log:Aws{eventName:flow2.eventName})
    where log1.additionalEventData_sub = log2.additionalEventData_sub
    AND log1.errorCode is null
        AND log2.errorCode is null
        AND log2.userAgent contains flow2.userAgent
        AND log2.eventSource = flow2.eventSource
    WITH datetime(log2.eventTime).epochSeconds as time2,
            datetime(log1.eventTime).epochSeconds as time1,
            flow1, flow2, rule, log1, log2
    WHERE log2.eventTime >= log1.eventTime
        AND time2 <= time1+1800
    WITH flow1, flow2, log1, log2, rule
    MERGE (log1)-[:CHECK{path:id(log1)+','+id(log2)}]->(flow1)
    MERGE (log2)-[:CHECK{path:id(log1)+','+id(log2)}]->(flow2)
    MERGE (log1)-[:FLOW{path:id(log1)+','+id(log2)}]->(log2)-[:FLOW_DETECTED{path:id(log1)+','+id(log2)}]->(rule)
    return log1, log2, rule"
    })
''',
'''
    MERGE (flow1:Flow:Aws {
        flowName : 'stop_instance',
        flowComment : 'EC2 인스턴스 중지',
        eventName : 'StopInstances'
    }) 
    MERGE (flow2:Flow:Aws {
        flowName : 'modify_ec2_user_data',
        flowComment : 'EC2 인스턴스 사용자 데이터 수정',
        eventName : 'ModifyInstanceAttribute'
    })
    MERGE (rule:Rule:Aws {
        ruleName : 'stop_ec2_modify_user_data',
        ruleComment : 'EC2 인스턴스 중지 후 사용자 데이터 수정',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        on_off : 1,
        level: 2,
        ruleType: 'default',
        ruleClass : 'dynamic',
        query: "MATCH (flow1:Flow:Aws {
        flowName : 'stop_instance',
        flowComment : 'EC2 인스턴스 중지',
        eventName : 'StopInstances'
    }) 
    MATCH (flow2:Flow:Aws {
        flowName : 'modify_ec2_user_data',
        flowComment : 'EC2 인스턴스 사용자 데이터 수정',
        eventName : 'ModifyInstanceAttribute'
    })
    MATCH (rule:Rule:Aws {
        ruleName : 'stop_ec2_modify_user_data',
        ruleComment : 'EC2 인스턴스 중지 후 사용자 데이터 수정',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        on_off : 1,
        level: 2,
        ruleType: 'default',
        ruleClass : 'dynamic'
    })
    WITH flow1, flow2, rule
    MATCH (log1:Log:Aws{eventName:flow1.eventName}), (log2:Log:Aws{eventName:flow2.eventName})
    WHERE ANY(key IN keys(log1) WHERE key =~ 'requestParameters_instancesSet_items_\\d+_instanceId' AND log1[key] contains log2.requestParameters_instanceId)
        AND log2.requestParameters_userData is not null
        AND log1.errorCode is null
        AND log2.errorCode is null
    WITH datetime(log2.eventTime).epochSeconds as time2,
            datetime(log1.eventTime).epochSeconds as time1,
            flow1, flow2, rule, log1, log2
    WHERE log2.eventTime >= log1.eventTime
        AND time2 <= time1+1800
    WITH flow1, flow2, log1, log2, rule
    MERGE (log1)-[:CHECK{path:id(log1)+','+id(log2)}]->(flow1)
    MERGE (log2)-[:CHECK{path:id(log1)+','+id(log2)}]->(flow2)
    MERGE (log1)-[:FLOW{path:id(log1)+','+id(log2)}]->(log2)-[:FLOW_DETECTED{path:id(log1)+','+id(log2)}]->(rule)
    return log1, log2, rule"
    })
''',
'''
    MERGE (flow1:Flow:Aws {
        flowName : 'register_task_curl',
        flowComment : '페이로드 수정해서 task definition 생성',
        eventName : 'RegisterTaskDefinition',
        requestParameters_containerDefinitions_command : 'curl'
    }) 
    MERGE (flow2:Flow:Aws {
        flowName : 'update_service_fargate',
        flowComment : 'fargate로 서비스 업데이트',
        eventName : 'UpdateService',
        responseElements_service_launchType : 'FARGATE'
    })
    MERGE (rule:Rule:Aws {
        ruleName : 'modify_payload_update_service',
        ruleComment : '페이로드 수정한 task definition 생성 후 자동 컨테이너 시작',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        on_off : 1,
        level: 3,
        ruleType: 'default',
        ruleClass : 'dynamic',
        query: "MATCH (flow1:Flow:Aws {
        flowName : 'register_task_curl',
        flowComment : '페이로드 수정해서 task definition 생성',
        eventName : 'RegisterTaskDefinition',
        requestParameters_containerDefinitions_command : 'curl'
    }) 
    MATCH (flow2:Flow:Aws {
        flowName : 'update_service_fargate',
        flowComment : 'fargate로 서비스 업데이트',
        eventName : 'UpdateService',
        responseElements_service_launchType : 'FARGATE'
    })
    MATCH (rule:Rule:Aws {
        ruleName : 'modify_payload_update_service',
        ruleComment : '페이로드 수정한 task definition 생성 후 자동 컨테이너 시작',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        on_off : 1,
        level: 3,
        ruleType: 'default',
        ruleClass : 'dynamic'
    })
    WITH flow1, flow2, rule
    MATCH (log1:Log:Aws{eventName:flow1.eventName}), (log2:Log:Aws{eventName:flow2.eventName})
    WHERE ANY(key IN keys(log1) WHERE key =~ 'requestParameters_containerDefinitions_\\d+_command_\\d' AND log1[key] contains flow1.requestParameters_containerDefinitions_command)
        AND log2.responseElements_service_launchType = flow2.responseElements_service_launchType
        AND log1.responseElements_taskDefinition_taskDefinitionArn = log2.requestParameters_taskDefinition
        AND log1.errorCode is null
        AND log2.errorCode is null
    WITH datetime(log2.eventTime).epochSeconds as time2,
            datetime(log1.eventTime).epochSeconds as time1,
            flow1, flow2, rule, log1, log2
    WHERE log2.eventTime >= log1.eventTime
        AND time2 <= time1+1800
    WITH flow1, flow2, log1, log2, rule
    MERGE (log1)-[:CHECK{path:id(log1)+','+id(log2)}]->(flow1)
    MERGE (log2)-[:CHECK{path:id(log1)+','+id(log2)}]->(flow2)
    MERGE (log1)-[:FLOW{path:id(log1)+','+id(log2)}]->(log2)-[:FLOW_DETECTED{path:id(log1)+','+id(log2)}]->(rule)
    return log1, log2, rule"
    })
''',
'''
    MERGE (flow1:Flow:Aws {
        flowName : 'create_instance_profile',
        flowComment : '새로운 인스턴스 프로파일 생성',
        eventName : 'CreateInstanceProfile'
    })
    MERGE (flow2:Flow:Aws {
        flowName : 'associate_profile_to_instance',
        flowComment : '인스턴스에 인스턴스 프로파일 연결',
        eventName : 'AssociateIamInstanceProfile'
    })
    MERGE (flow3:Flow:Aws {
        flowName : 'instance_assumedrole',
        flowComment : '인스턴스 접속 후 임시자격증명을 통해 행위',
        userIdentity_type : 'AssumedRole'
    })
    MERGE (rule:Rule:Aws {
        ruleName : 'new_instance_profile_act',
        ruleComment : '새로운 인스턴스 프로파일 추가 후 해당 프로파일을 사용해 인스턴스 행위',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        flow3 : flow3.flowName,
        on_off : 1,
        level: 3,
        ruleType: 'default',
        ruleClass : 'dynamic',
        query: "MATCH (flow1:Flow:Aws {
        flowName : 'create_instance_profile',
        flowComment : '새로운 인스턴스 프로파일 생성',
        eventName : 'CreateInstanceProfile'
    })
    MATCH (flow2:Flow:Aws {
        flowName : 'associate_profile_to_instance',
        flowComment : '인스턴스에 인스턴스 프로파일 연결',
        eventName : 'AssociateIamInstanceProfile'
    })
    MATCH (flow3:Flow:Aws {
        flowName : 'instance_assumedrole',
        flowComment : '인스턴스 접속 후 임시자격증명을 통해 행위',
        userIdentity_type : 'AssumedRole'
    })
    MATCH (rule:Rule:Aws {
        ruleName : 'new_instance_profile_act',
        ruleComment : '새로운 인스턴스 프로파일 추가 후 해당 프로파일을 사용해 인스턴스 행위',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        flow3 : flow3.flowName,
        on_off : 1,
        level: 3,
        ruleType: 'default',
        ruleClass : 'dynamic'
    })
    WITH flow1, flow2, flow3, rule
    MATCH (log1:Log:Aws{eventName:flow1.eventName}), (log2:Log:Aws{eventName:flow2.eventName}), (log3:Log:Aws)
    WHERE log3.userIdentity_arn contains log2.requestParameters_AssociateIamInstanceProfileRequest_InstanceId
        AND log3.userIdentity_arn contains log2.requestParameters_AssociateIamInstanceProfileRequest_IamInstanceProfile_Name
        AND log3.userIdentity_type = flow3.userIdentity_type
    AND log1.requestParameters_instanceProfileName = log2.requestParameters_AssociateIamInstanceProfileRequest_IamInstanceProfile_Name
        AND log1.errorCode is null
        AND log2.errorCode is null
    WITH datetime(log3.eventTime).epochSeconds as time3,
            datetime(log2.eventTime).epochSeconds as time2,
            datetime(log1.eventTime).epochSeconds as time1,
            flow1, flow2, flow3, rule, log1, log2, log3
    WHERE log3.eventTime >= log2.eventTime >= log1.eventTime
        AND time1 + 1800 >= time3 >= time1
    WITH flow1, flow2, log1, log2, log3, rule
    MERGE (log1)-[:CHECK{path:id(log1)+','+id(log2)+','+id(log3)}]->(flow1)
    MERGE (log2)-[:CHECK{path:id(log1)+','+id(log2)+','+id(log3)}]->(flow2)
    MERGE (log3)-[:CHECK{path:id(log1)+','+id(log2)+','+id(log3)}]->(flow3)
    MERGE (log1)-[:FLOW{path:id(log1)+','+id(log2)+','+id(log3)}]->(log2)-[:FLOW{path:id(log1)+','+id(log2)+','+id(log3)}]->(log3)-[:FLOW_DETECTED{path:id(log1)+','+id(log2)+','+id(log3)}]->(rule)
    return log1, log2, log3, rule"
    })
''',
'''
    MERGE (flow1:Flow:Aws {
        flowName : 'create_sg',
        flowComment : '보안 그룹 생성',
        eventName : 'CreateSecurityGroup'
    }) 
    MERGE (flow2:Flow:Aws {
        flowName : 'modify_db_instance_sg',
        flowComment : 'DB 보안 그룹 수정',
        eventName : 'ModifyDBInstance',
        responseElements_vpcSecurityGroups_status : 'adding'
    })
    MERGE (rule:Rule:Aws {
        ruleName : 'create_sg_modify_db_sg',
        ruleComment : '보안 그룹 생성 후 해당 보안 그룹으로 db 보안 그룹 수정',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        on_off : 1,
        level: 3,
        ruleType: 'default',
        ruleClass : 'dynamic',
        query: "MATCH (flow1:Flow:Aws {
        flowName : 'create_sg',
        flowComment : '보안 그룹 생성',
        eventName : 'CreateSecurityGroup'
    }) 
    MATCH (flow2:Flow:Aws {
        flowName : 'modify_db_instance_sg',
        flowComment : 'DB 보안 그룹 수정',
        eventName : 'ModifyDBInstance',
        responseElements_vpcSecurityGroups_status : 'adding'
    })
    MATCH (rule:Rule:Aws {
        ruleName : 'create_sg_modify_db_sg',
        ruleComment : '보안 그룹 생성 후 해당 보안 그룹으로 db 보안 그룹 수정',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        on_off : 1,
        level: 3,
        ruleType: 'default',
        ruleClass : 'dynamic'
    })
    WITH flow1, flow2, rule
    MATCH (log1:Log:Aws{eventName:flow1.eventName}), (log2:Log:Aws{eventName:flow2.eventName})
    WHERE ANY(key IN keys(log2) WHERE key =~ 'responseElements_vpcSecurityGroups_\\d+_vpcSecurityGroupId' AND log2[key] = log1.responseElements_groupId)
        AND ANY(key IN keys(log2) WHERE key =~ 'responseElements_vpcSecurityGroups_\\d+_status' AND log2[key] = 'adding')
    UNWIND [key IN keys(log2) WHERE key =~ 'responseElements_vpcSecurityGroups_(\\d+)_vpcSecurityGroupId' and log2[key] = log1.responseElements_groupId] as k
    WITH split(k, '_')[2] as num1, log1, log2, flow1, flow2, rule
    WHERE log2['responseElements_vpcSecurityGroups_' + num1 + '_status'] = 'adding'
        AND log1.errorCode is null
        AND log2.errorCode is null
    WITH datetime(log2.eventTime).epochSeconds as time2,
            datetime(log1.eventTime).epochSeconds as time1,
            flow1, flow2, rule, log1, log2
    WHERE log2.eventTime >= log1.eventTime
        AND time2 <= time1+1800
    WITH flow1, flow2, log1, log2, rule
    MERGE (log1)-[:CHECK{path:id(log1)+','+id(log2)}]->(flow1)
    MERGE (log2)-[:CHECK{path:id(log1)+','+id(log2)}]->(flow2)
    MERGE (log1)-[:FLOW{path:id(log1)+','+id(log2)}]->(log2)-[:FLOW_DETECTED{path:id(log1)+','+id(log2)}]->(rule)
    return log1, log2, rule"
    })
''',
'''
    MERGE (flow1:Flow:Aws {
        flowName : 'get_user',
        flowComment : '사용자 조회',
        eventName : 'GetUser',
        eventSource : 'cognito-idp.amazonaws.com'
    })
    MERGE (flow2:Flow:Aws {
        flowName : 'update_user_attributes',
        flowComment : 'aws-cli를 통해 수동으로 사용자 권한 속성 값 수정',
        eventName : 'UpdateUserAttributes',
        userAgent : 'aws-cli'
    })
    MERGE (rule:Rule:Aws {
        ruleName : 'cli_update_user_with_accessToken',
        ruleComment : 'accessToken을 통해 aws-cli에서 수동으로 사용자 권한 속성 값 수정',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        on_off : 1,
        level: 2,
        ruleType: 'default',
        ruleClass : 'dynamic',
        query: "MATCH (flow1:Flow:Aws {
        flowName : 'get_user',
        flowComment : '사용자 조회',
        eventName : 'GetUser',
        eventSource : 'cognito-idp.amazonaws.com'
    })
    MATCH (flow2:Flow:Aws {
        flowName : 'update_user_attributes',
        flowComment : 'aws-cli를 통해 수동으로 사용자 권한 속성 값 수정',
        eventName : 'UpdateUserAttributes',
        userAgent : 'aws-cli'
    })
    MATCH (rule:Rule:Aws {
        ruleName : 'cli_update_user_with_accessToken',
        ruleComment : 'accessToken을 통해 aws-cli에서 수동으로 사용자 권한 속성 값 수정',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        on_off : 1,
        level: 2,
        ruleType: 'default',
        ruleClass : 'dynamic'
    })
    WITH flow1, flow2, rule
    MATCH (log1:Log:Aws{eventName:flow1.eventName}), (log2:Log:Aws{eventName:flow2.eventName})
    WHERE log2.userAgent contains flow2.userAgent
        AND log1.eventSource = flow1.eventSource
    AND log1.additionalEventData_sub = log2.additionalEventData_sub 
        AND log1.errorCode is null
        AND log2.errorCode is null
    WITH datetime(log2.eventTime).epochSeconds as time2,
            datetime(log1.eventTime).epochSeconds as time1,
            flow1, flow2, rule, log1, log2
    WHERE log2.eventTime >= log1.eventTime
        AND time2 <= time1+1800
    WITH flow1, flow2, log1, log2, rule
    MERGE (log1)-[:CHECK{path:id(log1)+','+id(log2)}]->(flow1)
    MERGE (log2)-[:CHECK{path:id(log1)+','+id(log2)}]->(flow2)
    MERGE (log1)-[:FLOW{path:id(log1)+','+id(log2)}]->(log2)-[:FLOW_DETECTED{path:id(log1)+','+id(log2)}]->(rule)
    return log1, log2, rule"
    })
''',
'''
    MERGE (flow1:Flow:Aws {
        flowName : 'create_ebs_snapshot',
        flowComment : 'EBS 스냅샷 생성',
        eventName : 'CreateSnapshot'
    }) 
    MERGE (flow2:Flow:Aws {
        flowName : 'modify_ebs_snapshot',
        flowComment : 'EBS 스냅샷 속성 변경',
        eventName : 'ModifySnapshotAttribute'
    })
    MERGE (rule:Rule:Aws {
        ruleName : 'create_and_modify_snapshot',
        ruleComment : 'EBS 스냅샷을 만들고 속성 변경',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        on_off : 1,
        level: 3,
        ruleType: 'default',
        ruleClass : 'dynamic',
        query: "MATCH (flow1:Flow:Aws {
        flowName : 'create_ebs_snapshot',
        flowComment : 'EBS 스냅샷 생성',
        eventName : 'CreateSnapshot'
    }) 
    MATCH (flow2:Flow:Aws {
        flowName : 'modify_ebs_snapshot',
        flowComment : 'EBS 스냅샷 속성 변경',
        eventName : 'ModifySnapshotAttribute'
    })
    MATCH (rule:Rule:Aws {
        ruleName : 'create_and_modify_snapshot',
        ruleComment : 'EBS 스냅샷을 만들고 속성 변경',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        on_off : 1,
        level: 3,
        ruleType: 'default',
        ruleClass : 'dynamic'
    })
    WITH flow1, flow2, rule
    MATCH (log1:Log:Aws{eventName:flow1.eventName}), (log2:Log:Aws{eventName:flow2.eventName})
    WHERE log2.userIdentity_arn = log1.userIdentity_arn
        AND log1.responseElements_snapshotId = log2.requestParameters_snapshotId
        AND log1.errorCode is null
        AND log2.errorCode is null
    WITH datetime(log2.eventTime).epochSeconds as time2,
            datetime(log1.eventTime).epochSeconds as time1,
            flow1, flow2, rule, log1, log2
    WHERE log2.eventTime >= log1.eventTime
        AND time2 <= time1+1800
    WITH flow1, flow2, log1, log2, rule
    MERGE (log1)-[:CHECK{path:id(log1)+','+id(log2)}]->(flow1)
    MERGE (log2)-[:CHECK{path:id(log1)+','+id(log2)}]->(flow2)
    MERGE (log1)-[:FLOW{path:id(log1)+','+id(log2)}]->(log2)-[:FLOW_DETECTED{path:id(log1)+','+id(log2)}]->(rule)
    return log1, log2, rule"
    })
''',
'''
    MERGE (flow1:Flow:Aws {
        flowName : 'set_start_session_tag_true',
        flowComment : 'StartSeesion 태그 값 수동으로 true로 변경',
        eventName : 'CreateTags',
        requestParameters_tagSet_items_key : 'StartSession',
        requestParameters_tagSet_items_value : 'true'
    }) 
    MERGE (flow2:Flow:Aws {
        flowName : 'start_session',
        flowComment : '인스턴스에서 세션 시작',
        eventName : 'StartSession'
    })
    MERGE (rule:Rule:Aws {
        ruleName : 'set_tag_true_start_session',
        ruleComment : 'StartSession 태그 값 수동으로 true로 변경 후 해당 인스턴스에서 세션 시작',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        on_off : 1,
        level: 4,
        ruleType: 'default',
        ruleClass : 'dynamic',
        query: "MATCH (flow1:Flow:Aws {
        flowName : 'set_start_session_tag_true',
        flowComment : 'StartSeesion 태그 값 수동으로 true로 변경',
        eventName : 'CreateTags',
        requestParameters_tagSet_items_key : 'StartSession',
        requestParameters_tagSet_items_value : 'true'
    }) 
    MATCH (flow2:Flow:Aws {
        flowName : 'start_session',
        flowComment : '인스턴스에서 세션 시작',
        eventName : 'StartSession'
    })
    MATCH (rule:Rule:Aws {
        ruleName : 'set_tag_true_start_session',
        ruleComment : 'StartSession 태그 값 수동으로 true로 변경 후 해당 인스턴스에서 세션 시작',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        on_off : 1,
        level: 4,
        ruleType: 'default',
        ruleClass : 'dynamic'
    })
    WITH flow1, flow2, rule
    MATCH (log1:Log:Aws{eventName:flow1.eventName}), (log2:Log:Aws{eventName:flow2.eventName})
    WHERE ANY(key IN keys(log1) WHERE key =~ 'requestParameters_tagSet_items_\\d+_key' AND log1[key] = flow1.requestParameters_tagSet_items_key)
        AND ANY(key IN keys(log1) WHERE key =~ 'requestParameters_tagSet_items_\\d+_value' AND log1[key] = flow1.requestParameters_tagSet_items_value)
        AND ANY(key IN keys(log1) WHERE key =~ 'requestParameters_resourcesSet_items_\\d+_resourceId' AND log1[key] = log2.requestParameters_target)
    UNWIND [key IN keys(log1) WHERE key =~ 'requestParameters_tagSet_items_\\d+_key' and log1[key] = flow1.requestParameters_tagSet_items_key] as k
    WITH split(k, '_')[3] as num1, log1, log2, flow1, flow2, rule
    WHERE log1['requestParameters_tagSet_items_' + num1 + '_value'] = flow1.requestParameters_tagSet_items_value
        AND log1.errorCode is null
        AND log2.errorCode is null
    WITH datetime(log2.eventTime).epochSeconds as time2,
            datetime(log1.eventTime).epochSeconds as time1,
            flow1, flow2, rule, log1, log2
    WHERE log2.eventTime >= log1.eventTime
        AND time2 <= time1+1800
    WITH flow1, flow2, log1, log2, rule
    MERGE (log1)-[:CHECK{path:id(log1)+','+id(log2)}]->(flow1)
    MERGE (log2)-[:CHECK{path:id(log1)+','+id(log2)}]->(flow2)
    MERGE (log1)-[:FLOW{path:id(log1)+','+id(log2)}]->(log2)-[:FLOW_DETECTED{path:id(log1)+','+id(log2)}]->(rule)
    return log1, log2, rule"
    })
''',
'''
    MERGE (flow1:Flow:Aws {
        flowName : 'update_access_key',
        flowComment : '액세스 키 활성화',
        eventName : 'CreateAccessKey',
        responseElements_accessKey_status : 'Active'
    }) 
    MERGE (flow2:Flow:Aws {
        flowName : 'act_aws_cli',
        flowComment : 'aws cli를 통해 api 요청',
        userAgent : 'aws-cli'
    })
    MERGE (rule:Rule:Aws {
        ruleName : 'activate_access_key_awscli_call',
        ruleComment : '액세스 키 활성화 후 해당 user를 통해  aws-cli  및 api 요청',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        on_off : 1,
        level: 2,
        ruleType: 'default',
        ruleClass : 'dynamic',
        query: "MATCH (flow1:Flow:Aws {
        flowName : 'update_access_key',
        flowComment : '액세스 키 활성화',
        eventName : 'CreateAccessKey',
        responseElements_accessKey_status : 'Active'
    }) 
    MATCH (flow2:Flow:Aws {
        flowName : 'act_aws_cli',
        flowComment : 'aws cli를 통해 api 요청',
        userAgent : 'aws-cli'
    })
    MATCH (rule:Rule:Aws {
        ruleName : 'activate_access_key_awscli_call',
        ruleComment : '액세스 키 활성화 후 해당 user를 통해  aws-cli  및 api 요청',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        on_off : 1,
        level: 2,
        ruleType: 'default',
        ruleClass : 'dynamic'
    })
    WITH flow1, flow2, rule

    MATCH (log1:Log:Aws{eventName:flow1.eventName}), (log2:Log:Aws)
    WHERE log1.responseElements_accessKey_status = flow1.responseElements_accessKey_status 
    AND NOT log1.userIdentity_arn CONTAINS log1.requestParameters_userName
        AND log2.userIdentity_userName = log1.requestParameters_userName
        AND log2.userAgent contains flow2.userAgent
        AND log1.errorCode is null
        AND log2.errorCode is null
    WITH datetime(log2.eventTime).epochSeconds as time2,
            datetime(log1.eventTime).epochSeconds as time1,
            flow1, flow2, rule, log1, log2
    WHERE log2.eventTime >= log1.eventTime
        AND time2 <= time1+1800
    WITH flow1, flow2, log1, log2, rule
    MERGE (log1)-[:CHECK{path:id(log1)+','+id(log2)}]->(flow1)
    MERGE (log2)-[:CHECK{path:id(log1)+','+id(log2)}]->(flow2)
    MERGE (log1)-[:FLOW{path:id(log1)+','+id(log2)}]->(log2)-[:FLOW_DETECTED{path:id(log1)+','+id(log2)}]->(rule)
    return log1, log2, rule"
    })
''',
'''
    MERGE (flow1:Flow:Aws {
        flowName : 'create_function',
        flowComment : '람다 함수 생성',
        eventName : 'CreateFunction20150331'
    }) 
    MERGE (flow2:Flow:Aws {
        flowName : 'attach_policy_python',
        flowComment : 'python을 통해 전체관리자 권한 할당',
        eventName : 'AttachUserPolicy',
        userAgent : 'Boto3',
        requestParameters_policyArn : 'AdministratorAccess'
    })
    MERGE (rule:Rule:Aws {
        ruleName : 'create_function_attach_AA_policy',
        ruleComment : 'lambda 함수 생성 후 해당 함수 실행으로 전체관리자 권한 획득',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        on_off : 1,
        level: 3,
        ruleType: 'default',
        ruleClass : 'dynamic',
        query: "MATCH (flow1:Flow:Aws {
        flowName : 'create_function',
        flowComment : '람다 함수 생성',
        eventName : 'CreateFunction20150331'
    }) 
    MATCH (flow2:Flow:Aws {
        flowName : 'attach_policy_python',
        flowComment : 'python을 통해 전체관리자 권한 할당',
        eventName : 'AttachUserPolicy',
        userAgent : 'Boto3',
        requestParameters_policyArn : 'AdministratorAccess'
    })
    MATCH (rule:Rule:Aws {
        ruleName : 'create_function_attach_AA_policy',
        ruleComment : 'lambda 함수 생성 후 해당 함수 실행으로 전체관리자 권한 획득',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        on_off : 1,
        level: 3,
        ruleType: 'default',
        ruleClass : 'dynamic'
    })
    WITH flow1, flow2, rule

    MATCH (log1:Log:Aws{eventName:flow1.eventName}), (log2:Log:Aws{eventName:flow2.eventName})
    WHERE log2.userIdentity_principalId contains log1.requestParameters_functionName
        AND log2.requestParameters_policyArn contains flow2.requestParameters_policyArn
        AND log2.userAgent contains flow2.userAgent 
        AND log1.errorCode is null
        AND log2.errorCode is null
    WITH datetime(log2.eventTime).epochSeconds as time2,
            datetime(log1.eventTime).epochSeconds as time1,
            flow1, flow2, rule, log1, log2
    WHERE  log2.eventTime >= log1.eventTime
        AND time2 <= time1+1800
    WITH flow1, flow2, log1, log2, rule
    MERGE (log1)-[:CHECK{path:id(log1)+','+id(log2)}]->(flow1)
    MERGE (log2)-[:CHECK{path:id(log1)+','+id(log2)}]->(flow2)
    MERGE (log1)-[:FLOW{path:id(log1)+','+id(log2)}]->(log2)-[:FLOW_DETECTED{path:id(log1)+','+id(log2)}]->(rule)
    return log1, log2, rule"
    })
''',
'''
    MERGE (flow1:Flow:Aws {
        flowName : 'attach_policy_AA',
        flowComment : '사용자에게 전체관리자권한 부여',
        eventName : 'AttachUserPolicy',
        requestParameters_policyArn : 'AdministratorAccess'
    })
    MERGE (flow2:Flow:Aws {
        flowName : 'list_secrets',
        flowComment : 'secret list 조회',
        eventName : 'ListSecrets'
    })
    MERGE (flow3:Flow:Aws {
        flowName : 'get_secret_value',
        flowComment : 'secret 값 획득',
        eventName : 'GetSecretValue'
    })
    MERGE (rule:Rule:Aws {
        ruleName : 'attach_policy_get_secret',
        ruleComment : 'iam사용자가 전체관리자권한 부여 후 해당 사용자가 SecretList 확인 및 secretValue 획득',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        flow3 : flow3.flowName,
        on_off : 1,
        level: 4,
        ruleType: 'default',
        ruleClass : 'dynamic',
        query: "MATCH (flow1:Flow:Aws {
        flowName : 'attach_policy_AA',
        flowComment : '사용자에게 전체관리자권한 부여',
        eventName : 'AttachUserPolicy',
        requestParameters_policyArn : 'AdministratorAccess'
    })
    MATCH (flow2:Flow:Aws {
        flowName : 'list_secrets',
        flowComment : 'secret list 조회',
        eventName : 'ListSecrets'
    })
    MATCH (flow3:Flow:Aws {
        flowName : 'get_secret_value',
        flowComment : 'secret 값 획득',
        eventName : 'GetSecretValue'
    })
    MATCH (rule:Rule:Aws {
        ruleName : 'attach_policy_get_secret',
        ruleComment : 'iam사용자가 전체관리자권한 부여 후 해당 사용자가 SecretList 확인 및 secretValue 획득',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        flow3 : flow3.flowName,
        on_off : 1,
        level: 4,
        ruleType: 'default',
        ruleClass : 'dynamic'
    })
    WITH flow1, flow2, flow3, rule
    MATCH (log1:Log:Aws{eventName:flow1.eventName}), (log2:Log:Aws{eventName:flow2.eventName}), (log3:Log:Aws{eventName:flow3.eventName})
    WHERE log1.requestParameters_userName = log2. userIdentity_userName
        AND log2.userIdentity_userName = log3.userIdentity_userName
        AND log1.requestParameters_policyArn contains flow1.requestParameters_policyArn
        AND log1.errorcode is null
        AND log2.errorCode is null
        AND log3.errorCode is null
    WITH datetime(log3.eventTime).epochSeconds as time3, datetime(log2.eventTime).epochSeconds as time2,
            datetime(log1.eventTime).epochSeconds as time1,
            flow1, flow2, flow3, rule, log1, log2, log3
    WHERE log3.eventTime >= log2.eventTime >= log1.eventTime
        AND time1 + 1800 >= time2 >= time1
    WITH flow1, flow2, flow3, log1, log2, log3, rule
    MERGE (log1)-[:CHECK{path:id(log1)+','+id(log2)+','+id(log3)}]->(flow1)
    MERGE (log2)-[:CHECK{path:id(log1)+','+id(log2)+','+id(log3)}]->(flow2)
    MERGE (log3)-[:CHECK{path:id(log1)+','+id(log2)+','+id(log3)}]->(flow3)
    MERGE (log1)-[:FLOW{path:id(log1)+','+id(log2)+','+id(log3)}]->(log2)-[:FLOW{path:id(log1)+','+id(log2)+','+id(log3)}]->(log3)-[:FLOW_DETECTED{path:id(log1)+','+id(log2)+','+id(log3)}]->(rule)
    return log1, log2, log3, rule"
    })
''',
'''
    MERGE (flow1:Flow:Aws {
        flowName : 'create_role',
        flowComment : '새로운 역할 생성',
        eventName : 'CreateRole'
    }) 
    MERGE (flow2:Flow:Aws {
        flowName : 'switch_role',
        flowComment : '사용자 역할 변경',
        eventName : 'SwitchRole',
        userIdentity_accountId : '622751588873'
    })
    MERGE (rule:Rule:Aws {
        ruleName : 'create_role_assumed_by_aws_account',
        ruleComment : 'AWS Account에서 새롭게 생성한 Role로 역할 변경 후 aws 환경에 액세스',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        on_off : 1,
        level: 2,
        ruleType: 'default',
        ruleClass : 'dynamic',
        query: "MATCH (flow1:Flow:Aws {
        flowName : 'create_role',
        flowComment : '새로운 역할 생성',
        eventName : 'CreateRole'
    }) 
    MATCH (flow2:Flow:Aws {
        flowName : 'switch_role',
        flowComment : '사용자 역할 변경',
        eventName : 'SwitchRole',
        userIdentity_accountId : '622751588873'
    })
    MATCH (rule:Rule:Aws {
        ruleName : 'create_role_assumed_by_aws_account',
        ruleComment : 'AWS Account에서 새롭게 생성한 Role로 역할 변경 후 aws 환경에 액세스',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        on_off : 1,
        level: 2,
        ruleType: 'default',
        ruleClass : 'dynamic'
    })
    WITH flow1, flow2, rule

    MATCH (log1:Log:Aws{eventName:flow1.eventName}), (log2:Log:Aws{eventName:flow2.eventName})
    WHERE log2.userIdentity_arn contains log1.requestParameters_roleName
        AND split(log2.additionalEventData_SwitchFrom, ':')[4] <> flow2.userIdentity_accountId
        AND log1.errorcode is null
        AND log2.errorCode is null
    WITH datetime(log2.eventTime).epochSeconds as time2,
            datetime(log1.eventTime).epochSeconds as time1,
            flow1, flow2, rule, log1, log2
    WHERE log2.eventTime >= log1.eventTime
        AND time2 <= time1+1800
    WITH flow1, flow2, log1, log2, rule
    MERGE (log1)-[:CHECK{path:id(log1)+','+id(log2)}]->(flow1)
    MERGE (log2)-[:CHECK{path:id(log1)+','+id(log2)}]->(flow2)
    MERGE (log1)-[:FLOW{path:id(log1)+','+id(log2)}]->(log2)-[:FLOW_DETECTED{path:id(log1)+','+id(log2)}]->(rule)
    return log1, log2, rule"
    })
''',
'''
    MERGE (flow1:Flow:Aws {
        flowName : 'modify_sg_rule',
        flowComment : '방화벽 규칙 수정',
        eventName : ['AuthorizeSecurityGroupIngress','AuthorizeSecurityGroupEgress']
    }) 
    MERGE (flow2:Flow:Aws {
        flowName : 'run_instance',
        flowComment : '인스턴스 시작',
        eventName : 'RunInstances'
    })
    MERGE (rule:Rule:Aws {
        ruleName : 'run_instance_with_modify_sg',
        ruleComment : '방화벽 규칙 수정 후 해당 방화벽 규칙 할당해 인스턴스 시작',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        on_off : 1,
        level: 4,
        ruleType: 'default',
        ruleClass : 'dynamic',
        query: "MATCH (flow1:Flow:Aws {
        flowName : 'modify_sg_rule',
        flowComment : '방화벽 규칙 수정',
        eventName : ['AuthorizeSecurityGroupIngress','AuthorizeSecurityGroupEgress']
    }) 
    MATCH (flow2:Flow:Aws {
        flowName : 'run_instance',
        flowComment : '인스턴스 시작',
        eventName : 'RunInstances'
    })
    MATCH  (rule:Rule:Aws {
        ruleName : 'run_instance_with_modify_sg',
        ruleComment : '방화벽 규칙 수정 후 해당 방화벽 규칙 할당해 인스턴스 시작',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        on_off : 1,
        level: 4,
        ruleType: 'default',
        ruleClass : 'dynamic'
    })
    WITH flow1, flow2, rule

    MATCH (log1:Log:Aws), (log2:Log:Aws{eventName:flow2.eventName})
    WHERE log1.eventName in flow1.eventName
        AND ANY(key IN keys(log2) WHERE key =~ 'responseElements_instancesSet_items_\\d+_groupSet_items_\\d+_groupId' AND log2[key] =  log1.requestParameters_groupId)
        AND log1.errorcode is null
        AND log2.errorCode is null
    WITH datetime(log2.eventTime).epochSeconds as time2,
            datetime(log1.eventTime).epochSeconds as time1,
            flow1, flow2, rule, log1, log2
    WHERE log2.eventTime >= log1.eventTime
        AND time2 <= time1+1800
    WITH flow1, flow2, log1, log2, rule
    MERGE (log1)-[:CHECK{path:id(log1)+','+id(log2)}]->(flow1)
    MERGE (log2)-[:CHECK{path:id(log1)+','+id(log2)}]->(flow2)
    MERGE (log1)-[:FLOW{path:id(log1)+','+id(log2)}]->(log2)-[:FLOW_DETECTED{path:id(log1)+','+id(log2)}]->(rule)
    return log1, log2, rule"
    })
''',
'''
    MERGE (flow1:Flow:Aws {
        flowName : 'sign_up',
        flowComment : '사용자 등록',
        eventName : 'SignUp'
    })
    MERGE (flow2:Flow:Aws {
        flowName : 'user_not_confirmed',
        flowComment : '사용자 유효성 검사 오류',
        eventName : 'RespondToAuthChallenge',
        errorCode : 'UserNotConfirmedException'
    })
    MERGE (flow3:Flow:Aws {
        flowName : 'confirm_sign_up_cli',
        flowComment : 'aws-cli를 통해 수동으로 유효성 검사 우회',
        eventName : 'ConfirmSignUp',
        userAgent : 'aws-cli'
    })
    MERGE (rule:Rule:Aws {
        ruleName : 'cli_confirm_signup_after_error',
        ruleComment : '유효성 검사 오류 이후 aws cli를 통해 수동으로 계정 생성 및 유효성 검사 우회',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        flow3 : flow3.flowName,
        on_off : 1,
        level: 3,
        ruleType: 'default',
        ruleClass : 'dynamic',
        query: "MATCH (flow1:Flow:Aws {
        flowName : 'sign_up',
        flowComment : '사용자 등록',
        eventName : 'SignUp'
    })
    MATCH (flow2:Flow:Aws {
        flowName : 'user_not_confirmed',
        flowComment : '사용자 유효성 검사 오류',
        eventName : 'RespondToAuthChallenge',
        errorCode : 'UserNotConfirmedException'
    })
    MATCH (flow3:Flow:Aws {
        flowName : 'confirm_sign_up_cli',
        flowComment : 'aws-cli를 통해 수동으로 유효성 검사 우회',
        eventName : 'ConfirmSignUp',
        userAgent : 'aws-cli'
    })
    MATCH (rule:Rule:Aws {
        ruleName : 'cli_confirm_signup_after_error',
        ruleComment : '유효성 검사 오류 이후 aws cli를 통해 수동으로 계정 생성 및 유효성 검사 우회',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        flow3 : flow3.flowName,
        on_off : 1,
        level: 3,
        ruleType: 'default',
        ruleClass : 'dynamic'
    })
    WITH flow1, flow2, flow3, rule
    MATCH (log1:Log:Aws{eventName:flow1.eventName}), (log2:Log:Aws{eventName:flow2.eventName}), (log3:Log:Aws{eventName:flow3.eventName})
    WHERE log1.errorCode is null
        AND log1.requestParameters_clientId = log2.requestParameters_clientId = log3.requestParameters_clientId
        AND log2.errorCode = flow2.errorCode
        AND log3.userAgent contains flow3.userAgent
        AND log3.errorCode is null
    WITH datetime(log3.eventTime).epochSeconds as time3, datetime(log2.eventTime).epochSeconds as time2,
            datetime(log1.eventTime).epochSeconds as time1,
            flow1, flow2, flow3, rule, log1, log2, log3
    WHERE log3.eventTime >= log2.eventTime >= log1.eventTime
        AND time1 + 1800 >= time2 >= time1
    WITH flow1, flow2, flow3, log1, log2, log3, rule
    MERGE (log1)-[:CHECK{path:id(log1)+','+id(log2)+','+id(log3)}]->(flow1)
    MERGE (log2)-[:CHECK{path:id(log1)+','+id(log2)+','+id(log3)}]->(flow2)
    MERGE (log3)-[:CHECK{path:id(log1)+','+id(log2)+','+id(log3)}]->(flow3)
    MERGE (log1)-[:FLOW{path:id(log1)+','+id(log2)+','+id(log3)}]->(log2)-[:FLOW{path:id(log1)+','+id(log2)+','+id(log3)}]->(log3)-[:FLOW_DETECTED{path:id(log1)+','+id(log2)+','+id(log3)}]->(rule)
    return log1, log2, log3, rule"
    })
''',
'''
    MERGE (flow1:Flow:Aws {
        flowName : 'modify_network_acl_rule',
        flowComment : '네트워크 접근제어 규칙 수정',
        eventName : 'CreateNetworkAclEntry'
    }) 
    MERGE (flow2:Flow:Aws {
        flowName : 'replace_subnet_network_acl',
        flowComment : '서브넷 네트워크 접근제어 규칙 연결 수정',
        eventName : 'ReplaceNetworkAclAssociation'
    })
    MERGE (rule:Rule:Aws {
        ruleName : 'create_replace_network_acl',
        ruleComment : '네트워크 접근제어 규칙 수정 후 해당 Acl 로 서브넷 연결 수정',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        on_off : 1,
        level: 3,
        ruleType: 'default',
        ruleClass : 'dynamic',
        query: "MATCH (flow1:Flow:Aws {
        flowName : 'modify_network_acl_rule',
        flowComment : '네트워크 접근제어 규칙 수정',
        eventName : 'CreateNetworkAclEntry'
    }) 
    MATCH (flow2:Flow:Aws {
        flowName : 'replace_subnet_network_acl',
        flowComment : '서브넷 네트워크 접근제어 규칙 연결 수정',
        eventName : 'ReplaceNetworkAclAssociation'
    })
    MATCH (rule:Rule:Aws {
        ruleName : 'create_replace_network_acl',
        ruleComment : '네트워크 접근제어 규칙 수정 후 해당 Acl 로 서브넷 연결 수정',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        on_off : 1,
        level: 3,
        ruleType: 'default',
        ruleClass : 'dynamic'
    })
    WITH flow1, flow2, rule

    MATCH (log1:Log:Aws{eventName:flow1.eventName}), (log2:Log:Aws{eventName:flow2.eventName})
    WHERE log1.requestParameters_networkAclId = log2.requestParameters_networkAclId
        AND log1.errorCode is null
        AND log2.errorCode is null
    WITH datetime(log2.eventTime).epochSeconds as time2,
            datetime(log1.eventTime).epochSeconds as time1,
            flow1, flow2, rule, log1, log2
    WHERE log2.eventTime >= log1.eventTime
        AND time2 <= time1+1800
    WITH flow1, flow2, log1, log2, rule
    MERGE (log1)-[:CHECK{path:id(log1)+','+id(log2)}]->(flow1)
    MERGE (log2)-[:CHECK{path:id(log1)+','+id(log2)}]->(flow2)
    MERGE (log1)-[:FLOW{path:id(log1)+','+id(log2)}]->(log2)-[:FLOW_DETECTED{path:id(log1)+','+id(log2)}]->(rule)
    return log1, log2, rule"
    })
''',
'''
    MERGE (flow1:Flow:Aws {
        flowName : 'list_attached_role_policies',
        flowComment : '역할 할당 정책 조회',
        eventName : 'ListAttachedRolePolicies'
    }) 
    MERGE (flow2:Flow:Aws {
        flowName : 'attach_role_high_policy',
        flowComment : 'IAM 역할에 높은 권한 정책 할당',
        eventName : 'AttachRolePolicy',
        requestParameters_policyArn : ['AdministratorAccess','FullAccess']
    })
    MERGE (rule:Rule:Aws {
        ruleName : 'list_attached_role_policy_attach_high_policy',
        ruleComment : '역할 할당 정책 조회 후 높은 권한의 정책 추가',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        on_off : 1,
        level: 2,
        ruleType: 'default',
        ruleClass : 'dynamic',
        query: "MATCH (flow1:Flow:Aws {
        flowName : 'list_attached_role_policies',
        flowComment : '역할 할당 정책 조회',
        eventName : 'ListAttachedRolePolicies'
    }) 
    MATCH (flow2:Flow:Aws {
        flowName : 'attach_role_high_policy',
        flowComment : 'IAM 역할에 높은 권한 정책 할당',
        eventName : 'AttachRolePolicy',
        requestParameters_policyArn : ['AdministratorAccess','FullAccess']
    })
    MATCH (rule:Rule:Aws {
        ruleName : 'list_attached_role_policy_attach_high_policy',
        ruleComment : '역할 할당 정책 조회 후 높은 권한의 정책 추가',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        on_off : 1,
        level: 2,
        ruleType: 'default',
        ruleClass : 'dynamic'
    })
    WITH flow1, flow2, rule
    MATCH (log1:Log:Aws{eventName:flow1.eventName}), (log2:Log:Aws{eventName:flow2.eventName})
    WHERE log1.requestParameters_roleName  = log2.requestParameters_roleName 
        AND any(list in flow2.requestParameters_policyArn where log2.requestParameters_policyArn contains list)
        AND log1.errorCode is null
        AND log2.errorCode is null
    WITH datetime(log2.eventTime).epochSeconds as time2,
            datetime(log1.eventTime).epochSeconds as time1,
            flow1, flow2, rule, log1, log2
    WHERE log2.eventTime >= log1.eventTime
        AND time2 <= time1+1800
    WITH flow1, flow2, log1, log2, rule
    MERGE (log1)-[:CHECK{path:id(log1)+','+id(log2)}]->(flow1)
    MERGE (log2)-[:CHECK{path:id(log1)+','+id(log2)}]->(flow2)
    MERGE (log1)-[:FLOW]->(log2)-[:FLOW_DETECTED]->(rule)
    return log1, log2, rule"
    })
''',
'''
    MERGE (flow1:Flow:Aws {
        flowName : 'iam_remove_role_instance',
        flowComment : 'IAM 사용자가 인스턴스 프로필에서 역할 삭제',
        eventName : 'RemoveRoleFromInstanceProfile',
        userIdentity_type : 'IAMUser'
    }) 
    MERGE (flow2:Flow:Aws {
        flowName : 'iam_add_role_instance',
        flowComment : 'IAM 사용자가 인스턴스 프로필에 역할 할당',
        eventName : 'AddRoleToInstanceProfile',
        userIdentity_type : 'IAMUser'
    })
    MERGE (rule:Rule:Aws {
        ruleName : 'delete_role_create_role_same_profile',
        ruleComment : 'iam 사용자가 role 삭제 후 같은 프로필에 새로운 role 추가',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        on_off : 1,
        level: 1,
        ruleType: 'default',
        ruleClass : 'dynamic',
        query: "MATCH (flow1:Flow:Aws {
        flowName : 'iam_remove_role_instance',
        flowComment : 'IAM 사용자가 인스턴스 프로필에서 역할 삭제',
        eventName : 'RemoveRoleFromInstanceProfile',
        userIdentity_type : 'IAMUser'
    }) 
    MATCH (flow2:Flow:Aws {
        flowName : 'iam_add_role_instance',
        flowComment : 'IAM 사용자가 인스턴스 프로필에 역할 할당',
        eventName : 'AddRoleToInstanceProfile',
        userIdentity_type : 'IAMUser'
    })
    MATCH (rule:Rule:Aws {
        ruleName : 'delete_role_create_role_same_profile',
        ruleComment : 'iam 사용자가 role 삭제 후 같은 프로필에 새로운 role 추가',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        on_off : 1,
        level: 1,
        ruleType: 'default',
        ruleClass : 'dynamic'
    })
    WITH flow1, flow2, rule
    MATCH (log1:Log:Aws{eventName:flow1.eventName}), (log2:Log:Aws{eventName:flow2.eventName})
    WHERE log1.userIdentity_type = flow1.userIdentity_type
        AND log2.userIdentity_type = flow2.userIdentity_type
        AND log1.requestParameters_instanceProfileName = log2.requestParameters_instanceProfileName
        AND log1.requestParameters_roleName <> log2.requestParameters_roleName
        AND log1.errorCode is null
        AND log2.errorCode is null
    WITH datetime(log2.eventTime).epochSeconds as time2,
            datetime(log1.eventTime).epochSeconds as time1,
            flow1, flow2, rule, log1, log2
    WHERE log2.eventTime >= log1.eventTime
        AND time2 <= time1+1800
    WITH flow1, flow2, log1, log2, rule
    MERGE (log1)-[:CHECK{path:id(log1)+','+id(log2)}]->(flow1)
    MERGE (log2)-[:CHECK{path:id(log1)+','+id(log2)}]->(flow2)
    MERGE (log1)-[:FLOW{path:id(log1)+','+id(log2)}]->(log2)-[:FLOW_DETECTED{path:id(log1)+','+id(log2)}]->(rule)
    return log1, log2, rule"
    })
'''
]
flow_count = [
'''
    MERGE (flow1:Flow:Aws {
        flowName : 'multiple_get_policy_version',
        flowComment : '사용자 정책 버전별로 권한 확인',
        eventName : 'GetPolicyVersion'
    })
    WITH flow1

    match p=(firstLog:Log)-[:ACTED|NEXT*1..]->(log:Log)
    where firstLog.eventName= flow1.eventName
        AND log.eventName = flow1.eventName
        AND log.errorCode is null
        AND firstLog.errorCode is null
    WITH datetime(firstLog.eventTime).epochSeconds AS time1,
        datetime(log.eventTime).epochSeconds AS time2, log, firstLog, flow1
    WHERE log.eventTime >= firstLog.eventTime
        AND time2 <= time1+1800
    with collect(distinct(id(log))) as logs, id(firstLog) as firstLog, flow1
    WHERE size(logs) >= 4
    WITH logs, firstLog, flow1
    WITH collect(logs) AS c_logs, collect(firstLog) as c_firstLog, flow1
    unwind c_logs as u_c_logs
    with distinct(u_c_logs) as d_u_c_logs, c_logs, c_firstLog, flow1
    with apoc.coll.indexOf(c_logs, d_u_c_logs) as index, c_logs, c_firstLog, d_u_c_logs, flow1
    with d_u_c_logs, index, c_logs, c_firstLog, flow1
    call apoc.do.when(
        index <= 0,
        "
            return d_u_c_logs, c_firstLog[index] as i_c_firstLog
        ",
        " 
            with d_u_c_logs, c_logs[0..index] as i_logs,c_firstLog, c_logs
            UNWIND i_logs as i_log
            with apoc.coll.containsAll(i_log, d_u_c_logs) as contains, d_u_c_logs, c_logs, c_firstLog, i_log
            WHERE contains = true
            WITH COLLECT(i_log)[0] as i_log, c_firstLog, c_logs
            WITH apoc.coll.indexOf(c_logs, i_log) as index, c_logs, c_firstLog
            WITH c_logs[index] as d_u_c_logs, c_firstLog[index] as i_c_firstLog
            return d_u_c_logs, i_c_firstLog
        ",
    {c_logs : c_logs, index : index, d_u_c_logs : d_u_c_logs, c_firstLog:c_firstLog}
    ) yield value
    with DISTINCT(value.i_c_firstLog) as firstLog, value.d_u_c_logs AS logs, flow1
    with  firstLog, logs, last(logs) as l_logs, flow1

    MERGE (flow2:Flow:Aws {
        flowName : 'set_default_policy_version',
        flowComment : '정책 기본 버전 변경',
        eventName : 'SetDefaultPolicyVersion'
    })
    MERGE (rule:Rule:Aws {
        ruleName : 'set_default_policy_after_check_versions',
        ruleComment : 'iam 사용자가 특정 정책 버전별 권한 확인 후 해당 기본 버전 변경',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        on_off : 1,
        level: 2,
        ruleType: 'default',
        ruleClass : 'dynamic',
        query: "MATCH (flow1:Flow:Aws {
        flowName : 'multiple_get_policy_version',
        flowComment : '사용자 정책 버전별로 권한 확인',
        eventName : 'GetPolicyVersion'
    })
    WITH flow1

    match p=(firstLog:Log)-[:ACTED|NEXT*1..]->(log:Log)
    where firstLog.eventName= flow1.eventName
        AND log.eventName = flow1.eventName
        AND log.errorCode is null
        AND firstLog.errorCode is null
    WITH datetime(firstLog.eventTime).epochSeconds AS time1,
        datetime(log.eventTime).epochSeconds AS time2, log, firstLog, flow1
    WHERE log.eventTime >= firstLog.eventTime
        AND time2 <= time1+1800
    with collect(distinct(id(log))) as logs, id(firstLog) as firstLog, flow1
    WHERE size(logs) >= 4
    WITH logs, firstLog, flow1
    WITH collect(logs) AS c_logs, collect(firstLog) as c_firstLog, flow1
    unwind c_logs as u_c_logs
    with distinct(u_c_logs) as d_u_c_logs, c_logs, c_firstLog, flow1
    with apoc.coll.indexOf(c_logs, d_u_c_logs) as index, c_logs, c_firstLog, d_u_c_logs, flow1
    with d_u_c_logs, index, c_logs, c_firstLog, flow1
    call apoc.do.when(
        index <= 0,
        \\\"
            return d_u_c_logs, c_firstLog[index] as i_c_firstLog
    \\\",
        \\\" 
            with d_u_c_logs, c_logs[0..index] as i_logs,c_firstLog, c_logs
            UNWIND i_logs as i_log
            with apoc.coll.containsAll(i_log, d_u_c_logs) as contains, d_u_c_logs, c_logs, c_firstLog, i_log
            WHERE contains = true
            WITH COLLECT(i_log)[0] as i_log, c_firstLog, c_logs
            WITH apoc.coll.indexOf(c_logs, i_log) as index, c_logs, c_firstLog
            WITH c_logs[index] as d_u_c_logs, c_firstLog[index] as i_c_firstLog
            return d_u_c_logs, i_c_firstLog
        \\\",
    {c_logs : c_logs, index : index, d_u_c_logs : d_u_c_logs, c_firstLog:c_firstLog}
    ) yield value
    with DISTINCT(value.i_c_firstLog) as firstLog, value.d_u_c_logs AS logs, flow1
    with  firstLog, logs, last(logs) as l_logs, flow1

    MATCH (flow2:Flow:Aws {
        flowName : 'set_default_policy_version',
        flowComment : '정책 기본 버전 변경',
        eventName : 'SetDefaultPolicyVersion'
    })
    MATCH (rule:Rule:Aws {
        ruleName : 'set_default_policy_after_check_versions',
        ruleComment : 'iam 사용자가 특정 정책 버전별 권한 확인 후 해당 기본 버전 변경',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        on_off : 1,
        level: 2,
        ruleType: 'default',
        ruleClass : 'dynamic'
    })
    WITH flow1, flow2, rule, firstLog, logs, last(logs) as l_logs

    match(t_log:Log:Aws), (log2:Log:Aws{eventName:flow2.eventName})
    where id(t_log) = l_logs
        and log2.errorCode is null
    WITH datetime(log2.eventTime).epochSeconds as time2,
            datetime(t_log.eventTime).epochSeconds as time1,
            t_log, log2, firstLog, logs, last(logs) as l_logs, flow1, flow2, rule
    WHERE log2.eventTime >= t_log.eventTime
        AND time2 <= time1+1800
    WITH flow1, flow2, t_log, log2, rule, firstLog, logs, last(logs) as l_logs
    MERGE (t_log)-[:CHECK{path:id(t_log)+','+id(log2), firstLog:firstLog, flow: logs}]->(flow1)
    MERGE (log2)-[:CHECK{path:id(t_log)+','+id(log2)}]->(flow2)
    MERGE (t_log)-[:FLOW{path:id(t_log)+','+id(log2)}]->(log2)-[:FLOW_DETECTED{path:id(t_log)+','+id(log2)}]->(rule)
    return t_log, log2, rule, firstLog, logs, l_logs"
    })
'''
]
flow_ip = [
'''
    MERGE (flow1:Flow:Aws {
        flowName : 'login_without_mfa',
        flowComment : 'mfa 없이 콘솔 로그인',
        eventName : 'ConsoleLogin',
        additionalEventData_MFAUsed : 'No'
    })
    MERGE (flow2:Flow:Aws {
        flowName : 'acted_foreign',
        flowComment : '평소와 다른 국가에서 접속',
        country: 'KR'
    })
    MERGE (rule:Rule:Aws {
        ruleName : 'acted_foreign_after_login_without_mfa',
        ruleComment : 'MFA 없이 로그인한 사용자가 물리적으로 불가능한 거리에서 행위',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        on_off : 1,
        level: 2,
        ruleType: 'default',
        ruleClass : 'dynamic',
        query: "MATCH (flow1:Flow:Aws {
        flowName : 'login_without_mfa',
        flowComment : 'mfa 없이 콘솔 로그인',
        eventName : 'ConsoleLogin',
        additionalEventData_MFAUsed : 'No'
    })
    MATCH (flow2:Flow:Aws {
        flowName : 'acted_foreign',
        flowComment : '평소와 다른 국가에서 접속',
        country: 'KR'
    })
    MATCH (rule:Rule:Aws {
        ruleName : 'acted_foreign_after_login_without_mfa',
        ruleComment : 'MFA 없이 로그인한 사용자가 물리적으로 불가능한 거리에서 행위',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        on_off : 1,
        level: 2,
        ruleType: 'default',
        ruleClass : 'dynamic'
    })
    WITH flow1, flow2, rule
    MATCH (log1:Log:Aws{eventName:flow1.eventName}), (log2:Log:Aws{eventName:flow2.eventName})
    where log1.userIdentity_arn = log2.userIdentity_arn
    AND log1.errorCode is null
        AND log1.additionalEventData_MFAUsed contains flow2.additionalEventData_MFAUsed 
        AND log2.country <> flow2.country 
        ANd log2.country <> 'None'
    WITH datetime(log2.eventTime).epochSeconds as time2,
            datetime(log1.eventTime).epochSeconds as time1,
            flow1, flow2, rule, log1, log2
    WHERE log2.eventTime >= log1.eventTime
        AND time2 <= time1+1800
    WITH flow1, flow2, log1, log2, rule
    MERGE (log1)-[:CHECK{path:id(log1)+','+id(log2)}]->(flow1)
    MERGE (log2)-[:CHECK{path:id(log1)+','+id(log2)}]->(flow2)
    MERGE (log1)-[:FLOW{path:id(log1)+','+id(log2)}]->(log2)-[:FLOW_DETECTED{path:id(log1)+','+id(log2)}]->(rule)
    return log1, log2, rule"
    })
''',
'''
    MERGE (flow1:Flow:Aws {
        flowName : 'acted_iam',
        flowComment : 'iam 행위'
    })
    MERGE (flow2:Flow:Aws {
        flowName : 'acted_foreign_iam',
        flowComment : '이전과 다른 지역에서 행위'
    })
    MERGE (rule:Rule:Aws {
        ruleName : 'impossible_travel_iam',
        ruleComment : 'IAM사용자의 물리적으로 불가능한 이동 탐지',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        on_off : 1,
        level: 2,
        ruleType: 'default',
        ruleClass : 'dynamic',
        query: "MATCH (flow1:Flow:Aws {
        flowName : 'acted_iam',
        flowComment : 'iam 행위'
    })
    MATCH (flow2:Flow:Aws {
        flowName : 'acted_foreign_iam',
        flowComment : '이전과 다른 지역에서 행위'
    })
    MATCH (rule:Rule:Aws {
        ruleName : 'impossible_travel_iam',
        ruleComment : 'IAM사용자의 물리적으로 불가능한 이동 탐지',
        flow1 : flow1.flowName,
        flow2 : flow2.flowName,
        on_off : 1,
        level: 2,
        ruleType: 'default',
        ruleClass : 'dynamic'
    })
    WITH flow1, flow2, rule
    MATCH (log1:Log:Aws{eventName:flow1.eventName}), (log2:Log:Aws{eventName:flow2.eventName})
    where log1.userIdentity_arn = log2.userIdentity_arn
        AND log1.country <> 'None'
    AND log1.errorCode is null
        AND log2.country <> log1.country 
        ANd log2.country <> 'None'
    WITH datetime(log2.eventTime).epochSeconds as time2,
            datetime(log1.eventTime).epochSeconds as time1,
            flow1, flow2, rule, log1, log2
    WHERE log2.eventTime >= log1.eventTime
        AND time2 <= time1+1800
    WITH flow1, flow2, log1, log2, rule
    MERGE (log1)-[:CHECK{path:id(log1)+','+id(log2)}]->(flow1)
    MERGE (log2)-[:CHECK{path:id(log1)+','+id(log2)}]->(flow2)
    MERGE (log1)-[:FLOW{path:id(log1)+','+id(log2)}]->(log2)-[:FLOW_DETECTED{path:id(log1)+','+id(log2)}]->(rule)
    return log1, log2, rule"
    })
'''
]
flow_count_all = [
'''
    MERGE (rule:Rule:Aws {
        ruleName : 'multiple_access_denied',
        ruleComment : '권한 없는 특정 사용자로부터 30분 이내 5개 이상 오류 발생',
        errorCode : 'AccessDenied',
        level : 1,
        on_off : 1,
        ruleType : 'default',
        ruleClass : 'static',
        query: "MERGE (rule:Rule:Aws {
        ruleName : 'multiple_access_denied',
        ruleComment : '권한 없는 특정 사용자로부터 30분 이내 5개 이상 오류 발생',
        errorCode : 'AccessDenied',
        level : 1,
        on_off : 1,
        ruleType : 'default',
        ruleClass : 'static'
    })
    WITH rule

    match p=(firstLog:Log)-[:ACTED|NEXT*1..]->(log:Log)
    where firstLog.errorCode = rule.errorCode
        and log.errorCode = rule.errorCode
    WITH datetime(firstLog.eventTime).epochSeconds AS time1,
        datetime(log.eventTime).epochSeconds AS time2, log, firstLog, rule
    WHERE log.eventTime >= firstLog.eventTime
        AND time2 <= time1+3600
    with collect(distinct(id(log))) as logs, id(firstLog) as firstLog, rule
    WHERE size(logs) >= 4
    WITH logs, firstLog, rule
    WITH collect(logs) AS c_logs, collect(firstLog) as c_firstLog, rule
    unwind c_logs as u_c_logs
    with distinct(u_c_logs) as d_u_c_logs, c_logs, c_firstLog, rule
    with apoc.coll.indexOf(c_logs, d_u_c_logs) as index, c_logs, c_firstLog, d_u_c_logs, rule
    with d_u_c_logs, index, c_logs, c_firstLog, rule
    call apoc.do.when(
        index <= 0,
        \\\"
            return d_u_c_logs, c_firstLog[index] as i_c_firstLog
        \\\",
        \\\" 
            with d_u_c_logs, c_logs[0..index] as i_logs,c_firstLog, c_logs
            UNWIND i_logs as i_log
            with apoc.coll.containsAll(i_log, d_u_c_logs) as contains, d_u_c_logs, c_logs, c_firstLog, i_log
            WHERE contains = true
            WITH COLLECT(i_log)[0] as i_log, c_firstLog, c_logs
            WITH apoc.coll.indexOf(c_logs, i_log) as index, c_logs, c_firstLog
            WITH c_logs[index] as d_u_c_logs, c_firstLog[index] as i_c_firstLog
            return d_u_c_logs, i_c_firstLog
    \\\",
    {c_logs : c_logs, index : index, d_u_c_logs : d_u_c_logs, c_firstLog:c_firstLog}
    ) yield value
    with DISTINCT(value.i_c_firstLog) as firstLog, value.d_u_c_logs AS logs, rule
    with firstLog, logs, last(logs) as l_logs, rule

    match(t_log:Log)
    where id(t_log) = l_logs
    merge (t_log)-[:DETECTED{firstLog:firstLog, flow: logs}]->(rule)
    return t_log, rule"
    })
'''
]
flow_count_iam = [
'''
    MERGE (rule:Rule:Aws {
        ruleName : 'modify_multiple_iam_policy',
        ruleComment : '비정상적으로 많은 양의 IAM 정책 변경 사항 탐지',
        eventName : ['AttachUserPolicy', 'DetachUserPolicy','DeleteUserPolicy','PutUserPolicy'],
        eventSource: 'iam.amazonaws.com',
        level : 2,
        on_off : 1,
        ruleType : 'default',
        ruleClass : 'static',
        query: "MATCH (rule:Rule:Aws {
        ruleName : 'modify_multiple_iam_policy',
        ruleComment : '비정상적으로 많은 양의 IAM 정책 변경 사항 탐지',
        eventName : ['AttachUserPolicy', 'DetachUserPolicy','DeleteUserPolicy','PutUserPolicy'],
        eventSource: 'iam.amazonaws.com',
        level : 2,
        on_off : 1,
        ruleType : 'default',
        ruleClass : 'static'
    })
    WITH rule

    match p=(firstLog:Log)-[:ACTED|NEXT*1..]->(log:Log)
    where firstLog.eventName in rule.eventName
    and log.eventName in rule.eventName
        and firstLog.eventSource = rule.eventSource
    and log.eventSource = rule.eventSource
        and firstLog.errorCode is null
        and log.errorCode is null
    WITH datetime(firstLog.eventTime).epochSeconds AS time1,
        datetime(log.eventTime).epochSeconds AS time2, log, firstLog, rule
    WHERE log.eventTime >= firstLog.eventTime
    AND time2 <= time1+1800
    with collect(distinct(id(log))) as logs, id(firstLog) as firstLog, rule
    WHERE size(logs) >= 4
    WITH logs, firstLog, rule
    WITH collect(logs) AS c_logs, collect(firstLog) as c_firstLog, rule
    unwind c_logs as u_c_logs
    with distinct(u_c_logs) as d_u_c_logs, c_logs, c_firstLog, rule
    with apoc.coll.indexOf(c_logs, d_u_c_logs) as index, c_logs, c_firstLog, d_u_c_logs, rule
    with d_u_c_logs, index, c_logs, c_firstLog, rule
    call apoc.do.when(
        index <= 0,
        \\\"
            return d_u_c_logs, c_firstLog[index] as i_c_firstLog
        \\\",
    \\\" 
            with d_u_c_logs, c_logs[0..index] as i_logs,c_firstLog, c_logs
            UNWIND i_logs as i_log
            with apoc.coll.containsAll(i_log, d_u_c_logs) as contains, d_u_c_logs, c_logs, c_firstLog, i_log
            WHERE contains = true
            WITH COLLECT(i_log)[0] as i_log, c_firstLog, c_logs
            WITH apoc.coll.indexOf(c_logs, i_log) as index, c_logs, c_firstLog
            WITH c_logs[index] as d_u_c_logs, c_firstLog[index] as i_c_firstLog
            return d_u_c_logs, i_c_firstLog
        \\\",
    {c_logs : c_logs, index : index, d_u_c_logs : d_u_c_logs, c_firstLog:c_firstLog}
    ) yield value
    with DISTINCT(value.i_c_firstLog) as firstLog, value.d_u_c_logs AS logs, rule
    with firstLog, logs, last(logs) as l_logs, rule

    match(t_log:Log)
    where id(t_log) = l_logs
    merge (t_log)-[:DETECTED{firstLog:firstLog, flow: logs}]->(rule)
    return t_log, rule"
    })
'''
]
flow_count_sts = [
'''
    MERGE (rule:Rule:Aws {
        ruleName : 'multiple_assume_role',
        ruleComment : '특정 사용자로부터 임시 자격증명 요청 이벤트 다수 발생',
        eventName : 'AssumeRole',
        userIdentity_type:'IAMUser',
        eventSource : 'sts.amazonaws.com',
        level : 2,
        on_off : 1,
        ruleType : 'default',
        ruleClass : 'static',
        query: "MATCH (rule:Rule:Aws {
        ruleName : 'multiple_assume_role',
        ruleComment : '특정 사용자로부터 임시 자격증명 요청 이벤트 다수 발생',
        eventName : 'AssumeRole',
        userIdentity_type:'IAMUser',
        eventSource : 'sts.amazonaws.com',
        level : 2,
        on_off : 1,
        ruleType : 'default',
        ruleClass : 'static'
    })
    WITH rule

    match p=(firstLog:Log)-[:ACTED|NEXT*1..]->(log:Log)
    where firstLog.eventName = rule.eventName
    and log.eventName = rule.eventName
        and firstLog.userIdentity_type = rule.userIdentity_type
    and log.userIdentity_type = rule.userIdentity_type
        and firstLog.eventSource = rule.eventSource
    and log.eventSource = rule.eventSource
    WITH datetime(firstLog.eventTime).epochSeconds AS time1,
        datetime(log.eventTime).epochSeconds AS time2, log, firstLog, rule
    WHERE log.eventTime >= firstLog.eventTime
    AND time2 <= time1+1800
    with collect(distinct(id(log))) as logs, id(firstLog) as firstLog, rule
    WHERE size(logs) >= 4
    WITH logs, firstLog, rule
    WITH collect(logs) AS c_logs, collect(firstLog) as c_firstLog, rule
    unwind c_logs as u_c_logs
    with distinct(u_c_logs) as d_u_c_logs, c_logs, c_firstLog, rule
    with apoc.coll.indexOf(c_logs, d_u_c_logs) as index, c_logs, c_firstLog, d_u_c_logs, rule
    with d_u_c_logs, index, c_logs, c_firstLog, rule
    call apoc.do.when(
        index <= 0,
        \\\"
            return d_u_c_logs, c_firstLog[index] as i_c_firstLog
        \\\",
        \\\" 
            with d_u_c_logs, c_logs[0..index] as i_logs,c_firstLog, c_logs
            UNWIND i_logs as i_log
            with apoc.coll.containsAll(i_log, d_u_c_logs) as contains, d_u_c_logs, c_logs, c_firstLog, i_log
            WHERE contains = true
            WITH COLLECT(i_log)[0] as i_log, c_firstLog, c_logs
            WITH apoc.coll.indexOf(c_logs, i_log) as index, c_logs, c_firstLog
            WITH c_logs[index] as d_u_c_logs, c_firstLog[index] as i_c_firstLog
            return d_u_c_logs, i_c_firstLog
        \\\",
    {c_logs : c_logs, index : index, d_u_c_logs : d_u_c_logs, c_firstLog:c_firstLog}
    ) yield value
    with DISTINCT(value.i_c_firstLog) as firstLog, value.d_u_c_logs AS logs, rule
    with firstLog, logs, last(logs) as l_logs, rule

    match(t_log:Log)
    where id(t_log) = l_logs
    merge (t_log)-[:DETECTED{firstLog:firstLog, flow: logs}]->(rule)
    return t_log, rule"
    })
'''
]
flow_count_ec2 =[
'''
    MERGE (rule:Rule:Aws {
        ruleName : 'get_pwd_data',
        ruleComment : '실행 중인 윈도우 인스턴스들의 비밀번호 검색 및 출력',
        eventName : 'GetPasswordData',
        eventSource : 'ec2.amazonaws.com',
        level : 2,
        on_off : 1,
        ruleType : 'default',
        ruleClass : 'static',
        query: "MERGE (rule:Rule:Aws {
        ruleName : 'get_pwd_data',
        ruleComment : '실행 중인 윈도우 인스턴스들의 비밀번호 검색 및 출력',
        eventName : 'GetPasswordData',
        eventSource : 'ec2.amazonaws.com',
        level : 2,
        on_off : 1,
        ruleType : 'default',
        ruleClass : 'static'
    })
    WITH rule

    match p=(firstLog:Log)-[:ACTED|NEXT*1..]->(log:Log)
    where firstLog.eventName = rule.eventName
    and log.eventName = rule.eventName
        and firstLog.eventSource = rule.eventSource
    and log.eventSource = rule.eventSource
    WITH datetime(firstLog.eventTime).epochSeconds AS time1,
        datetime(log.eventTime).epochSeconds AS time2, log, firstLog, rule
    WHERE log.eventTime >= firstLog.eventTime
    AND time2 <= time1+1800
    with collect(distinct(id(log))) as logs, id(firstLog) as firstLog, rule
    WHERE size(logs) >= 3
    WITH logs, firstLog, rule
    WITH collect(logs) AS c_logs, collect(firstLog) as c_firstLog, rule
    unwind c_logs as u_c_logs
    with distinct(u_c_logs) as d_u_c_logs, c_logs, c_firstLog, rule
    with apoc.coll.indexOf(c_logs, d_u_c_logs) as index, c_logs, c_firstLog, d_u_c_logs, rule
    with d_u_c_logs, index, c_logs, c_firstLog, rule
    call apoc.do.when(
        index <= 0,
        \\\"
            return d_u_c_logs, c_firstLog[index] as i_c_firstLog
        \\\",
        \\\" 
            with d_u_c_logs, c_logs[0..index] as i_logs,c_firstLog, c_logs
            UNWIND i_logs as i_log
            with apoc.coll.containsAll(i_log, d_u_c_logs) as contains, d_u_c_logs, c_logs, c_firstLog, i_log
            WHERE contains = true
            WITH COLLECT(i_log)[0] as i_log, c_firstLog, c_logs
            WITH apoc.coll.indexOf(c_logs, i_log) as index, c_logs, c_firstLog
            WITH c_logs[index] as d_u_c_logs, c_firstLog[index] as i_c_firstLog
            return d_u_c_logs, i_c_firstLog
        \\\",
    {c_logs : c_logs, index : index, d_u_c_logs : d_u_c_logs, c_firstLog:c_firstLog}
    ) yield value
    with DISTINCT(value.i_c_firstLog) as firstLog, value.d_u_c_logs AS logs, rule
    with firstLog, logs, last(logs) as l_logs, rule

    match(t_log:Log)
    where id(t_log) = l_logs
    merge (t_log)-[:DETECTED{firstLog:firstLog, flow: logs}]->(rule)
    return t_log, rule"
    })
'''
]

flow_rule_detect_query = []
merge_flow_query_list = ['flow_default', 
                         'flow_count', 
                         'flow_ip', 
                         'flow_count_all', 
                         'flow_count_iam', 
                         'flow_count_sts', 
                         'flow_count_ec2'
                   ]

for query_name in merge_flow_query_list:
    current_list = globals().get(query_name)
    flow_rule_detect_query.extend(current_list)