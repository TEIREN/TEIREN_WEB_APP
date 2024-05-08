test_ecs = [
'''
    MERGE (rule:Rule:Aws {
        ruleName : 'first_time_execute_command',
        ruleComment : '사용자가 ECS 컨테이너에서 처음으로 명령어 실행',
        eventName : 'ExecuteCoammand',
        eventSource : 'ecs.amazonaws.com',
        level : 1,
        on_off : 1,
        ruleType : 'default',
        ruleClass : 'static',
        logType : 'cloudtrail',
        query: "MATCH (rule:Rule:Aws {
        ruleName : 'first_time_execute_command',
        ruleComment : '사용자가 ECS 컨테이너에서 처음으로 명령어 실행',
        eventName : 'ExecuteCoammand',
        eventSource : 'ecs.amazonaws.com',
        level : 1,
        on_off : 1,
        ruleType : 'default',
        ruleClass : 'static',
        logType : 'cloudtrail'
    })
    WITH rule
    MATCH (log:Log:Aws)
    WHERE log.eventName = rule.eventName
        AND log.eventsource = rule.eventsource
    OPTIONAL MATCH (l:Log:Aws{eventName:'ExecuteCommand', requestParameters_containerName : log.requestParameters_containerName})
        AND l.eventTime < log.eventTime
    WITH l, log, rule
    call apoc.do.when(
        l is null,
        \\\"merge (log)-[:DETECTED]->(rule) return log\\\",
        \\\"return log\\\",
        {log:log, rule:rule, l:l}
    ) yield value
    return value.log"
    })
'''
]
count_test_all = [
'''
    MERGE (rule:Rule:Aws {
        ruleName : 'multiple_authorization_failure',
        ruleComment : '특정 사용자로부터 인증 실패 이벤트가 5개 이상 발생',
        errorCode : 'AuthorizationFailure',
        level : 1,
        on_off : 1,
        ruleType : 'default',
        ruleClass : 'static',
        query: "MATCH (rule:Rule:Aws {
        ruleName : 'multiple_authorization_failure',
        ruleComment : '특정 사용자로부터 인증 실패 이벤트가 5개 이상 발생',
        errorCode : 'AuthorizationFailure',
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
    merge (t_log)-[:DETECTED{firstLog:firstLog, flow: logs}]->(rule)"
    })
''',
'''
    MERGE (rule:Rule:Aws {
        ruleName : 'multiple_ec2_error',
        ruleComment : 'ec2 인스턴스로부터 다수의 인증 실패 이벤트 발생',
        userIdentity_type:'AssumedRole',
        userIdentity_principal : 'i-',
        errorCode : 'AuthorizationFailure',
        level : 2,
        on_off : 1,
        ruleType : 'default',
        ruleClass : 'static',
        query: "MATCH (rule:Rule:Aws {
        ruleName : 'multiple_ec2_error',
        ruleComment : 'ec2 인스턴스로부터 다수의 인증 실패 이벤트 발생',
        userIdentity_type:'AssumedRole',
        userIdentity_principal : 'i-',
        errorCode : 'AuthorizationFailure',
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
    and firstLog.errorCode = rule.errorCode
    and log.errorCode = rule.errorCode
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
count_test_signin =[
'''
    MERGE (rule:Rule:Aws {
        ruleName : 'brute_force_console_login',
        ruleComment : 'brute force 로그인 공격 의심 행위',
        eventName : 'ConsoleLogin',
        eventSource: 'signin.amazonaws.com',
        level : 1,
        on_off : 1,
        ruleType : 'default',
        ruleClass : 'static',
        query: "MATCH (rule:Rule:Aws {
        ruleName : 'brute_force_console_login',
        ruleComment : 'brute force 로그인 공격 의심 행위',
        eventName : 'ConsoleLogin',
        eventSource: 'signin.amazonaws.com',
        level : 1,
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
            and firstLog.errorCode is not null
            and log.errorCode is not null
    WITH datetime(firstLog.eventTime).epochSeconds AS time1,
        datetime(log.eventTime).epochSeconds AS time2, log, firstLog, rule
    WHERE log.eventTime >= firstLog.eventTime
        AND time2 <= time1+1800
    with collect(distinct(id(log))) as logs, id(firstLog) as firstLog, rule
    WHERE size(logs) >= 9
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
count_test_apigateway = [
'''
    MERGE (rule:Rule:Aws {
        ruleName : 'get_api_keys_multiple',
        ruleComment : '특정사용자로부터 API Gateway API Key 값 요청 이벤트 다수 발생',
        eventName : 'GetApiKeys',
        eventSource: 'apigateway.amazonaws.com',
        level : 3,
        on_off : 1,
        ruleType : 'default',
        ruleClass : 'static',
        query: "MATCH (rule:Rule:Aws {
        ruleName : 'get_api_keys_multiple',
        ruleComment : '특정사용자로부터 API Gateway API Key 값 요청 이벤트 다수 발생',
        eventName : 'GetApiKeys',
        eventSource: 'apigateway.amazonaws.com',
        level : 3,
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
count_test_cognito = [
'''
    MERGE (rule:Rule:Aws {
        ruleName : 'muliple_comfirm_signup_failure',
        ruleComment : '사용자 유효성 검사 여러 번 실패',
        eventName : 'ConfirmSignUp',
        eventSource: 'cognito-idp.amazonaws.com',
        level : 1,
        on_off : 1,
        ruleType : 'default',
        ruleClass : 'static',
        query: "MATCH (rule:Rule:Aws {
        ruleName : 'muliple_comfirm_signup_failure',
        ruleComment : '사용자 유효성 검사 여러 번 실패',
        eventName : 'ConfirmSignUp',
        eventSource: 'cognito-idp.amazonaws.com',
        level : 1,
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
        and firstLog.errorCode is not null
    and log.errorCode is not null
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
count_test_s3 =[
'''
    MERGE (rule:Rule:Aws {
        ruleName : 'multiple_assumed_role_s3_events',
        ruleComment : '특정 사용자로부터 임시 자격증명을 통해 s3 버킷 관련 다수 발생',
        userIdentity_type : 'AssumedRole',
        eventSource: 's3.amazonaws.com',
        level : 2,
        on_off : 1,
        ruleType : 'default',
        ruleClass : 'static',
        query: "MATCH (rule:Rule:Aws {
        ruleName : 'multiple_assumed_role_s3_events',
        ruleComment : '특정 사용자로부터 임시 자격증명을 통해 s3 버킷 관련 다수 발생',
        userIdentity_type : 'AssumedRole',
        eventSource: 's3.amazonaws.com',
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
count_test_ec2 = [
'''
    MERGE (rule:Rule:Aws {
        ruleName : 'run_multiple_cpu',
        ruleComment : '30분 내에 지나치게 많은 수의 ec2 인스턴스 생성',
        eventName : 'RunInstances',
        eventSource: 'ec2.amazonaws.com',
        level : 3,
        on_off : 1,
        ruleType : 'default',
        ruleClass : 'static',
        query: "MATCH (rule:Rule:Aws {
        ruleName : 'run_multiple_cpu',
        ruleComment : '30분 내에 지나치게 많은 수의 ec2 인스턴스 생성',
        eventName : 'RunInstances',
        eventSource: 'ec2.amazonaws.com',
        level : 3,
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
count_test_ip = [
'''
    MERGE (rule:Rule:Aws {
        ruleName : 'multiple_foreign_access',
        ruleComment : '30분 동안 다양한 ip대역에서 클라우드 환경 접근',
        level : 2,
        on_off : 1,
        ruleType : 'default',
        ruleClass : 'static',
        query: "MATCH (rule:Rule:Aws {
        ruleName : 'multiple_foreign_access',
        ruleComment : '30분 동안 다양한 ip대역에서 클라우드 환경 접근',
        level : 2,
        on_off : 1,
        ruleType : 'default',
        ruleClass : 'static'
    })
    WITH rule

    match p=(firstLog:Log)-[:ACTED|NEXT*1..]->(log:Log)
    where firstLog.country <> log.country
    WITH datetime(firstLog.eventTime).epochSeconds AS time1,
        datetime(log.eventTime).epochSeconds AS time2, log, firstLog, rule
    WHERE log.eventTime >= firstLog.eventTime
        AND time2 <= time1+1800
    with collect(distinct(id(log))) as logs, collect(distinct(log.country) as countrys, id(firstLog) as firstLog, rule
    WHERE size(logs) >= 4
        AND size(countrys) >= 4
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
    merge (t_log)-[:DETECTED{firstLog:firstLog, flow: logs}]->(rule)"
    })
'''
]

test_rule_detect_query = []
merge_test_query_list = ['test_ecs', 
                         'count_test_all', 
                         'count_test_signin', 
                         'count_test_apigateway', 
                         'count_test_cognito', 
                         'count_test_s3', 
                         'count_test_ec2',
                         'count_test_ip'
                   ]

for query_name in merge_test_query_list:
    current_list = globals().get(query_name)
    test_rule_detect_query.extend(current_list)