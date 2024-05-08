from django.conf import settings
from py2neo import Graph, ClientError
from django.http import QueryDict
import json
## LOCAL
# graph = Graph("bolt://127.0.0.1:7687", auth=('neo4j', 'teiren001'))

## NCP
# host = settings.NEO4J_HOST
# port = settings.NEO4J_PORT
# password = settings.NEO4J_PASSWORD
# username = settings.NEO4J_USERNAME

## AWS
host = settings.NEO4J['HOST']
port = settings.NEO4J["PORT"]
username = settings.NEO4J['USERNAME']
password = settings.NEO4J['PASSWORD']
graph = Graph(f"bolt://{host}:{port}", auth=(username, password))

## Add Rule Modal
# Get Log Properties for Adding Custom Rule
def get_log_properties(request):
    cloud = request['cloud']
    global graph
    cypher = f"""
    MATCH (l:Log:{cloud})-[:DETECTED]->()
    WITH KEYS(l) AS keys
    RETURN apoc.coll.toSet(REDUCE(res = [], k IN COLLECT(DISTINCT(keys)) | res + k)) AS property
    """
    results = graph.evaluate(cypher)
    return results

# List Default Rule Actions for Adding Custom Rule
def get_default_actions(request):
    cloud = request['cloud']
    global graph
    cypher = f"""
        MATCH (r:Rule:{cloud})
        WHERE NOT 'FLOW' in LABELS(r)
        RETURN r.ruleName as ruleName
    """
    results = graph.run(cypher)
    response = []
    for result in results:
        response.append(result['ruleName'])
    return response

# Add Rule Action
def add_rule(request):
    ruleClass = request.pop('ruleClass')
    if ruleClass == 'static':
        request.pop('count')
        return add_static_rule(request)
    elif ruleClass == 'dynamic':
        return add_dynamic_rule(request)

# Static Rules
def add_static_rule(request):
    cloud = request['cloud']
    rule = {'key': [], 'value':[], 'operator':[]}
    for key, value in request.items():
        if 'Name' in key:
            if not value:
                return "정책 이름을 입력해주세요"
            else:
                if 'og_rule_name' not in request:
                    cypher = f"MATCH (r:Rule:{cloud} {{ruleName:'{value}'}}) RETURN COUNT(r)"
                    if graph.evaluate(cypher):
                        return "같은 이름의 정책이 존재합니다"
        elif 'Comment' in key:
            if not value:
                    return "정책 설명을 입력해주세요"
        elif 'custom' in key:
            if value:
                rule['key'] += [value]
                continue
            else:
                return f"정책 속성 {key[-1]}: 새로운 정책 속성을 입력해주세요"
        elif 'val' in key:
            if not value:
                return f"정책 속성 값 {key[-1]}을 입력해주세요"
            elif value:
                rule['value'] += [value]
                continue
        elif 'key' in key:
            if value:
                if f"정책 속성 {key[-1]}" in value:
                    return f"정책 속성 {key[-1]}을 선택해주세요"
                if f"새로운 정책 속성" in value:
                    continue
                rule['key'] += [value]
                continue
            else:
                return f"정책 속성 {key[-1]}을 선택해주세요"
        elif any(i in key for i in ['Count', 'time']):
            if value:
                try:
                    value = int(value)
                except:
                    return "탐지 횟수 및 시간 범위는 숫자로만 입력 가능합니다."
        elif key == 'cloud':
            continue
        if value:
            if 'property' in key:
                if 'logical' in key:
                    if 'logical' not in rule:
                        rule['logical'] = []
                    rule['logical'] += [value]
                elif 'op_' in key:
                    rule['operator'] += [value]
                else:
                    rule['property'][key.split('_', 1)[1]] = value
            else:
                rule[key] = value
    if ('ruleCount' in rule) != ('timeRange' in rule):
        return "탐지 횟수와 시간 범위를 모두 입력해주세요. \n(원하시지 않으면 두 입력란 모두 비워주세요)"
    if 'check' in request:
        request.pop('check')
        return 1
    result = static_cypher(rule, cloud)
    return result

def static_cypher(rule, cloud):
    rule_properties = ""
    where_cypher = ""
    for i in range(0, len(rule['key'])):
        rule_properties += f"{rule['key'][i]}:'{rule['value'][i]}', "
        where_cypher += f"toLower(log.{rule['key'][i]}) {rule['operator'][i]} toLower(rule.{rule['key'][i]})"
        if 'logical' in rule and len(rule['logical']) > i:
            where_cypher += f" {rule['logical'][i]} "
    rule_properties += f"ruleOperators: {rule['operator']}, ruleKeys: {rule['key']}, ruleValues: {rule['value']}, "
    rule_properties += f"ruleLogicals: {rule['logical']}, " if 'logical' in rule else ''
    cypher = f"""
    MERGE (rule:Rule:{cloud}
        {{
            ruleName: '{rule['ruleName']}',
            ruleComment: '{rule['ruleComment']}',
            on_off: 1,
            level: {rule['ruleLevel']},
            {rule_properties}
            ruleClass: 'static',
            ruleType: 'custom',
            ruleCount: '{rule['ruleCount'] if 'ruleCount' in rule else 1}',
            timeRange: '{rule['timeRange'] if 'timeRange' in rule else 0}'
        }}
    )
    WITH rule
    """
    if 'ruleCount' in rule:
        cypher += static_count_cypher(where_cypher, rule)
    else:
        cypher += f"""
        MATCH (log:Log:{cloud})
        WHERE
            log.errorCode IS NULL AND
            {where_cypher}
        WITH rule, log
        MERGE (log)-[:DETECTED]->(rule)
        """
    result = rule_merge_test(cypher, rule, cloud, 'static')
    return result

def static_count_cypher(where_cypher, rule):
    count_cypher = f"""
    MATCH p=(firstLog:Log)-[:ACTED|NEXT*1..]->(log:Log)
    WHERE
        log.errorCode IS NULL AND
        {where_cypher}
    WITH datetime(firstLog.eventTime).epochSeconds AS time1,
    datetime(log.eventTime).epochSeconds AS time2, log, firstLog, rule
    WHERE log.eventTime >= firstLog.eventTime
        AND time2 <= time1+{rule['timeRange']}
    WITH collect(distinct(id(log))) AS logs, id(firstLog) AS firstLog, rule
    WHERE SIZE(logs) >= {rule['ruleCount']}
    WITH logs, firstLog, rule
    WITH collect(logs) AS c_logs, collect(firstLog) AS c_firstLog, rule
    unwind c_logs AS u_c_logs
    WITH distinct(u_c_logs) AS d_u_c_logs, c_logs, c_firstLog, rule
    WITH apoc.coll.indexOf(c_logs, d_u_c_logs) AS index, c_logs, c_firstLog, d_u_c_logs, rule
    WITH d_u_c_logs, index, c_logs, c_firstLog, rule
    call apoc.do.when(
        index <= 0,
        '
            RETURN d_u_c_logs, c_firstLog[index] AS i_c_firstLog
        ',
        ' 
            WITH d_u_c_logs, c_logs[0..index] AS i_logs,c_firstLog, c_logs
            UNWIND i_logs AS i_log
            WITH apoc.coll.containsAll(i_log, d_u_c_logs) as contains, d_u_c_logs, c_logs, c_firstLog, i_log
            WHERE contains = true
            WITH COLLECT(i_log)[0] as i_log, c_firstLog, c_logs
            WITH apoc.coll.indexOf(c_logs, i_log) AS index, c_logs, c_firstLog
            WITH c_logs[index] as d_u_c_logs, c_firstLog[index] AS i_c_firstLog
            RETURN d_u_c_logs, i_c_firstLog
        ',
    {{c_logs : c_logs, index : index, d_u_c_logs : d_u_c_logs, c_firstLog:c_firstLog}}
    ) yield value
    WITH DISTINCT(value.i_c_firstLog) as firstLog, value.d_u_c_logs AS logs, rule
    WITH firstLog, logs, last(logs) as l_logs, rule

    MATCH (t_log:Log)
    WHERE id(t_log) = l_logs
    MERGE (t_log)-[:DETECTED{{firstLog:firstLog, path: logs}}]->(rule)
    """
    return count_cypher

# Dynamic Rules
def get_flow_check(request):
    flows = QueryDict(request['rules']).dict()
    count = int(request['rule_count'])
    for i in range(1, count+1):
        for key, value in flows.items():
            if key[-3] == str(i):
                if f'name_{i}' in key:
                    if not value:
                        return f"error 탐지 정책 {i}의 이름을 입력해주세요"
                    else:
                        if f'flow_og_{i}_1' in flows:
                            if flows[f'flow_og_{i}_1'] == value:
                                continue
                        if graph.evaluate(f"MATCH (flow:Flow {{flowName: '{value}'}}) RETURN COUNT(flow)") > 0:
                            return f"error 탐지 정책 {i}: 같은 이름의 탐지 정책이 존재합니다. 탐지 정책 이름을 변경해주세요."
                if f'comment_{i}' in key:
                    if not value:
                        return f"error 탐지 정책 {i}의 설명을 입력해주세요"
                if f'count_{i}' in key:
                    if value:
                        try:
                            value = int(value)
                        except:
                            return f"error 탐지 정책 {i}: 탐지 횟수는 숫자로만 입력이 가능합니다"
                if not value or value == f'탐지 정책 속성':
                    if f'key_{i}' in key:
                        return f"error 탐지 정책 {i}의 속성을 입력해주세요"
                    if f'val_{i}' in key:
                        return f"error 탐지 정책 {i}의 속성 값을 입력해주세요"
                    if f'custom_{i}' in key:
                        return f"error 탐지 정책 {i}의 새로운 탐지 정책 속성을 입력해주세요"
    return get_flow_slot(request)

def get_flow_slot(request):
    flows = QueryDict(request['rules']).dict()
    count = int(request['rule_count'])
    rules = {}
    for i in range(1, count+1):
        for key, value in flows.items():
            if str(i) not in rules:
                rules[f'{i}'] = {}
                keys = []
                values = []
            if any(i in key for i in [f'key_{i}', f'custom_{i}']):
                if value in keys:
                    return f"탐지 정책 {i}: 한 탐지 정책에 같은 속성을 선택할 수 없습니다"
                if value == '새로운 탐지 정책 속성':
                    continue
                keys.append(value)
            if f'val_{i}' in key:
                values.append(value)
        items = [[keys[i], values[i]] for i in range(len(keys))]
        rules[f'{i}']['item'] = items
    result = {'flows': rules}
    if 'wheres' in request:
        result['wheres'] = json.loads(request['wheres'])
    return result

def add_dynamic_rule(request):
    cloud = request['cloud']
    count = int(request['count'])
    rule = {}
    flows = {}
    wheres = {}
    for key, value in request.items():
        if 'ruleName' in key:
            if not value:
                return "정책 이름을 입력해주세요"
            else:
                if 'og_rule_name' not in request:
                    if graph.evaluate(f" MATCH (rule:Rule {{ruleName:'{value}'}}) RETURN count(rule)") > 0 :
                        return "같은 이름의 정책이 존재합니다. 정책 이름을 변경해주세요."
            rule[key] = value
        if 'ruleComment' in key:
            if not value:
                return "정책 설명을 입력해주세요"
            rule[key] = value
        if 'timeRange' in key:
            if not value:
                return "탐지 시간 범위를 초단위로 입력해주세요"
            try:
                value = int(value)
            except:
                return "탐지 시간 범위는 숫자로만 입력 가능합니다"
            rule[key] = value
        if 'ruleLevel' in key:
            rule[key] = value
        if any(i in key for i in ['flow_src', 'flow_op', 'flow_dst', 'flow_logical']):
            if not value:
                return f"탐지 {key[-1]}의 탐지 로그 속성을 선택해주세요"
            if f'{key[-1]}' not in wheres:
                wheres[f'{key[-1]}'] = {}
            wheres[f'{key[-1]}'][key.split('_')[1]] = value
            continue
        if 'flow' in key:
            if value:
                if f'{key[-3]}' not in flows:
                    flows[f'{key[-3]}'] = {'key':[], 'val':[]}
                if 'custom_' in key:
                    flows[f'{key[-3]}']['key'].append(value)
                if any(i in key for i in ['key_', 'val_']):
                    if value == '새로운 탐지 정책 속성':
                        continue
                    flows[f'{key[-3]}'][key.split('_')[1]].append(value)
                    continue
                if 'name_' in key:
                    if 'og_rule_name' not in request:
                        if graph.evaluate(f"MATCH (flow:Flow {{flowName:'{value}'}}) RETURN COUNT(flow)") > 0:
                            return f"탐지 정책 {key[-3]}: 같은 이름의 탐지 정책이 존재합니다. 탐지 정책 이름을 변경해주세요."
                flows[f'{key[-3]}'][key.split('_')[1]] = value
    if 'check' in request:
        request.pop('check')
        return 1
    cypher = dynamic_cypher(flows, wheres, rule, count, cloud)
    result = rule_merge_test(cypher, rule, cloud, 'dynamic')
    return result

def dynamic_cypher(flows, wheres, rule, count, cloud):
    ## Merge & Match Cypher
    cypher = ''
    where_cypher = 'WHERE '
    with_cypher = 'rule'
    match_cypher = 'MATCH '
    time_cypher = ''
    flow_reverse = []
    ### adding flow cypher
    for i, flow in flows.items():
        prop_cypher = ""
        for item in range(len(flow['key'])):
            prop_cypher += f"{', ' if item != 0 else ''}{flow['key'][item]}: '{flow['val'][item]}'"
        cypher += f"""
        MERGE (flow{i}:Flow:{cloud}{{
            {prop_cypher},
            flowName: '{flow['name']}',
            flowComment: '{flow['comment']}'
            {f", count: {flow['count']}" if 'count' in flow else ''}
        }})
        """
        with_cypher += f', flow{i}'
        if 'count' in flow:
            match_cypher += f"{'' if i == '1' else ', '}(log{i}:Log:{cloud})"
            where_cypher += f"{'' if i == '1' else ' AND '}ID(log{i}) = l_logs{i} AND log{i}.errorCode IS NULL"
        else:
            match_cypher += f"{'' if i == '1' else ', '}(log{i}:Log:{cloud}{{{prop_cypher}}})"
            where_cypher += f"{'' if i == '1' else ' AND '}log{i}.errorCode IS NULL"
        time_cypher += f', log{i}, datetime(log{i}.eventTime).epochSeconds AS time{i}'
        flow_reverse = [i] + flow_reverse
    ### where cypher
    where_prop = []
    for i, where in wheres.items():
        if where['srcNum'] == where['dstNum'] and where['srcProperty'] == where['dstProperty']:
            return f"탐지 {i}: 서로 다른 값을 선택해주세요"
        query = f"{' AND' if i == '1' else ''} {where['srcNum']}.{where['srcProperty']} {where['op']} {where['dstNum']}.{where['dstProperty']} "
        if 'logical' in where:
            query += where['logical']
        where_cypher += query
        where_prop.append(where)
    for prop in where_prop.copy():
        where_prop.remove(prop)
        where_prop.append("{" + ", ".join(f"{k}:{v}" for k, v in prop.items()) + "}")
        # where_prop.append(str(type(prop)))
    ### adding rule cypher
    flow_names = ''
    for i in range(1, count+1):
        flow_names += f"flow{i}: flow{i}.flowName, "
    cypher += f"""
    MERGE (rule:Rule:{cloud}{{
        {flow_names}
        ruleName:'{rule['ruleName']}',
        ruleComment:'{rule['ruleComment']}',
        level: {rule['ruleLevel']},
        on_off: 1,
        timeRange: {rule['timeRange']},
        ruleType: 'custom',
        ruleClass : 'dynamic',
        wheres: {where_prop}
    }})
    """
    cypher += 'WITH ' + with_cypher
    ### dynamic count match cypher
    count_cyphers = []
    for i, flow in flows.items():
        if 'count' in flow:
            count_cypher, with_cypher = dynamic_count_cypher(flow, i, rule, with_cypher)
            count_cyphers.append(count_cypher)
    for count_cypher in count_cyphers:
        cypher += '\n' + count_cypher
    
    ### adding with & match & where cypher
    cypher += '\n' + match_cypher
    cypher += '\n' + where_cypher
    ## Detection & Connection Cypher
    ### where time cypher
    cypher += '\n WITH ' + with_cypher + time_cypher
    where_time_cypher = 'WHERE '
    for i in flow_reverse:
        where_time_cypher += f'log{i}.eventTime '
        if i != '1':
            where_time_cypher += '>= '
        else:
            where_time_cypher += 'AND '
    where_time_cypher += f"time{flow_reverse[0]}<=time1+{rule['timeRange']}"
    cypher += '\n' + where_time_cypher
    cypher += '\nWITH '
    for i in flow_reverse:
        cypher += f'flow{i}, log{i}, '
    cypher += 'rule'
    ### merge connection cypher
    detection_path = ''
    for i in range(1, count+1):
        detection_path += f"id(log{i})+','+"
    detection_path = detection_path[0:-5]
    merge_cypher = 'MERGE '
    for i in range(1, count+1):
        cypher += f"""
        MERGE (log{i})-[:CHECK{{path:{detection_path}}}]->(flow{i})
        """
        merge_cypher += f"{'' if i == 1 else f'-[:FLOW{{path:{detection_path}}}]->'}(log{i})"
    merge_cypher += f'-[:FLOW_DETECTED{{path:{detection_path}}}]->(rule)'
    cypher += merge_cypher
    return cypher

def dynamic_count_cypher(flow, i, rule, with_cypher):
    count_where_cypher = ''
    for item in range(len(flow['key'])):
        count_where_cypher += f""" firstLog.{flow['key'][item]}= flow{i}.{flow['key'][item]}
        AND log.{flow['key'][item]} = flow{i}.{flow['key'][item]}
        AND """
    count_cypher = f"""
    MATCH p=(firstLog:Log)-[:ACTED|NEXT*1..]->(log:Log)
    WHERE
        {count_where_cypher}log.errorCode IS NULL
        AND firstLog.errorCode IS NULL
    WITH datetime(firstLog.eventTime).epochSeconds AS time1,
        datetime(log.eventTime).epochSeconds AS time2, log, firstLog, {with_cypher}
    WHERE log.eventTime >= firstLog.eventTime
        AND time2 <= time1+{rule['timeRange']}
    WITH COLLECT(DISTINCT(ID(log))) AS logs, ID(firstLog) AS firstLog, {with_cypher}
    WHERE SIZE(logs) >= {flow['count']}
    WITH logs, firstLog, {with_cypher}
    WITH COLLECT(logs) AS c_logs, COLLECT(firstLog) AS c_firstLog, {with_cypher}
    UNWIND c_logs AS u_c_logs
    WITH DISTINCT(u_c_logs) AS d_u_c_logs, c_logs, c_firstLog, {with_cypher}
    WITH apoc.coll.indexOf(c_logs, d_u_c_logs) AS index, c_logs, c_firstLog, d_u_c_logs, {with_cypher}
    WITH d_u_c_logs, index, c_logs, c_firstLog, {with_cypher}
    CALL apoc.do.when(
        index <= 0,
        '
            RETURN d_u_c_logs, c_firstLog[index] AS i_c_firstLog
        ',
        ' 
            WITH d_u_c_logs, c_logs[0..index] AS i_logs,c_firstLog, c_logs
            UNWIND i_logs AS i_log
            WITH apoc.coll.containsAll(i_log, d_u_c_logs) AS contains, d_u_c_logs, c_logs, c_firstLog, i_log
            WHERE contains = true
            WITH COLLECT(i_log)[0] AS i_log, c_firstLog, c_logs
            WITH apoc.coll.indexOf(c_logs, i_log) AS index, c_logs, c_firstLog
            WITH c_logs[index] AS d_u_c_logs, c_firstLog[index] AS i_c_firstLog
            RETURN d_u_c_logs, i_c_firstLog
        ',
    {{c_logs : c_logs, index : index, d_u_c_logs : d_u_c_logs, c_firstLog:c_firstLog}}
    ) YIELD value
    WITH DISTINCT(value.i_c_firstLog) AS firstLog{i}, value.d_u_c_logs AS logs{i}, {with_cypher}
    WITH firstLog{i}, logs{i}, last(logs{i}) AS l_logs{i}, {with_cypher}
    """
    with_cypher += f', firstLog{i}, logs{i}, l_logs{i}'
    return count_cypher, with_cypher

def rule_merge_test(cypher, rule, cloud, ruleClass):
    try:
        graph.evaluate(cypher)
    except ClientError as e:
        return f"{e}"+ '정책 추가를 실패했습니다. 정책을 다시 검토하고 저장해주세요.'
    rule_cypher = f"""
    MATCH (rule:Rule:{cloud}
        {{
            ruleName: '{rule['ruleName']}',
            ruleComment: '{rule['ruleComment']}',
            ruleClass: '{ruleClass}',
            ruleType: 'custom'
        }}
    )
    SET rule.query = "{cypher}"
    RETURN COUNT(rule)
    """
    try:
        if graph.evaluate(rule_cypher) == 1:
            return '정책 추가 완료'
    except ClientError as e:
        return f"{e}"#'정책 추가 실패'