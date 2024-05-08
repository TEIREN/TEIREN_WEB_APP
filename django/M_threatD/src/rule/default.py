from django.conf import settings
from py2neo import Graph, ClientError

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

# List All Rules
def get_all_rules():
    cypher = f"""
    MATCH (r:RULE:AWS)
    RETURN
        id(r) as id,
        HEAD([label IN labels(r) WHERE label <> 'RULE' AND label <> 'FLOW']) as label,
        CASE
            WHEN 'FLOW' IN labels(r) THEN 'FLOW'
            ELSE split(r.eventSource, '.')[0]
        END as log_type,
        r.ruleName as name,
        r.ruleComment as comment,
        r.level as level,
        r.on_off as on_off,
        r.ruleType as rule_type
    """
    results = graph.run(cypher)
    data = []
    for result in results:
        data.append(dict(result))
    response = {'rules': data}
    return response

# List Filters
def get_filter_list(logType):
    ruleType_list = graph.evaluate(f"""
    MATCH (r:Rule:{logType.split('_')[0].capitalize()})
    WITH
        CASE
            WHEN r.ruleClass = 'dynamic' THEN 'Dynamic'
            WHEN r.eventSource IS NULL THEN 'All'
            WHEN r.ruleClass IS NULL OR r.ruleClass = 'static' THEN split(r.eventSource,'.')[0]
            ELSE split(r.eventSource, '.')[0]
        END AS ruleType
    RETURN COLLECT(DISTINCT(ruleType))
    """)

    ruleName_list = graph.evaluate(f"""
    MATCH (r:Rule:{logType.split('_')[0].capitalize()})
    WHERE r.ruleName IS NOT NULL
    RETURN COLLECT(DISTINCT(r.ruleName))
    """)
    
    response = {
        'ruleType_list': ruleType_list,
        'ruleName_list': ruleName_list
    }

    return response

# List Default Rules
def get_default_rules(logType):
    cypher= f"""
    MATCH (r:Rule:{logType.split('_')[0].capitalize()} {{ruleType: 'default'}})
    RETURN
    id(r) as id,
    CASE
        WHEN r.ruleClass = 'dynamic' THEN 'Dynamic'
        WHEN r.eventSource IS NULL THEN 'All'
        WHEN r.ruleClass IS NULL OR r.ruleClass = 'static' THEN split(r.eventSource,'.')[0]
        ELSE split(r.eventSource, '.')[0]
    END as type,
    r.ruleName as name,
    r.ruleComment as comment,
    CASE
        WHEN r.level = 1 THEN ['LOW', 'success']
        WHEN r.level = 2 THEN ['MID', 'warning']
        WHEN r.level = 3 THEN ['HIGH', 'caution']
        ELSE ['CRITICAL', 'danger']
    END AS level,
    r.on_off as on_off
    """
    results = graph.run(cypher)
    data = []
    for result in results:
        data.append(dict(result.items()))
    response = {'default': data}
    return response

# List Custom Rules
def get_custom_rules(logType):
    cypher= f"""
    MATCH (r:Rule:{logType.split('_')[0].capitalize()} {{ruleType: 'custom'}})
    RETURN
    id(r) as id,
    CASE
        WHEN r.ruleClass = 'dynamic' THEN 'Dynamic'
        WHEN r.eventSource IS NULL THEN 'All'
        WHEN r.ruleClass IS NULL OR r.ruleClass = 'static' THEN split(r.eventSource,'.')[0]
        ELSE split(r.eventSource, '.')[0]
    END as type,
    r.ruleName as name,
    r.ruleComment as comment,
    CASE
        WHEN r.level = 1 THEN ['LOW', 'success']
        WHEN r.level = 2 THEN ['MID', 'warning']
        WHEN r.level = 3 THEN ['HIGH', 'caution']
        ELSE ['CRITICAL', 'danger']
    END AS level,
    r.on_off as on_off
    """
    results = graph.run(cypher)
    data = []
    for result in results:
        data.append(dict(result.items()))
    response = {'custom': data}
    return response

# Filtered Rules
def get_filtered_rules(logType, ruleType, request:dict):
    filter_dict = {}
    for key, value in request.items():
        if key == 'severity':
            print(value)
        if value[0] == '' or value[0] == 'all' or key == 'main_search_value' or key.endswith('regex') or key in filter_dict:
            continue
        elif key.startswith('main'):
            if request['main_search_value'][0] != '':
                filter_dict[value[0]] = ['regex',f".*{request['main_search_value'][0]}.*"]
            continue
        elif value[0] == 'regex':
            value.append(request[f'{key}_regex'][0])
        filter_dict[key] = value
    
    where_cypher = 'WHERE '
    if ruleType == 'default':
        for key, value in filter_dict.items():
            where_cypher += "AND " if len(where_cypher) != 6 else ""
            if value[0] == 'regex':
                where_cypher += f"{key} =~ '{value[1]}' "
            else:
                for val in value:
                    if key in ['severity','on_off']:
                        where_cypher += f"{key} = {val} "
                    else:
                        where_cypher += f"{key} = '{val}' "

    cypher= f"""
    MATCH (r:Rule:{logType.split('_')[0].capitalize()} {{ruleType: '{ruleType}'}})
    WITH
        id(r) as id,
        CASE
            WHEN r.ruleClass = 'dynamic' THEN 'Dynamic'
            WHEN r.eventSource IS NULL THEN 'All'
            WHEN r.ruleClass IS NULL OR r.ruleClass = 'static' THEN split(r.eventSource,'.')[0]
            ELSE split(r.eventSource, '.')[0]
        END as ruleType,
        r.ruleName as ruleName,
        r.ruleComment as comment,
        CASE
            WHEN r.level = 1 THEN ['LOW', 'success']
            WHEN r.level = 2 THEN ['MID', 'warning']
            WHEN r.level = 3 THEN ['HIGH', 'caution']
            ELSE ['CRITICAL', 'danger']
        END AS severity,
        r.on_off as on_off
    {where_cypher if len(where_cypher) > 6 else ''}
    RETURN
        id, ruleType AS type, ruleName AS name, comment, severity AS level, on_off
    """
    results = graph.run(cypher)
    data = []
    for result in results:
        data.append(dict(result.items()))
    response = {f'{ruleType}': data}
    return response

# Rule On Off
def rule_on_off(request):
    logType = request['log_type'].split(' ')[0].capitalize()
    rule_name = request['rule_name']
    on_off = request['on_off']
    cypher = f"""
    MATCH (r:Rule:{logType} {{ruleName:'{rule_name}'}})
    SET r.on_off = {abs(int(on_off)-1)}
    RETURN r
    """
    try:
        graph.evaluate(cypher)
        if abs(int(on_off)-1) == 1:
            graph.run(f"""
            MATCH (r:Rule:{logType} {{ruleName:'{rule_name}'}})
            SET r.status = 'Add'
            RETURN r
            """)
        else:
            graph.run(f"""
            MATCH (r:Rule:{logType} {{ruleName:'{rule_name}'}})
            WITH ID(r) AS nodeId
            MERGE (d:Rule {{status:'Delete', nodeId: nodeId}})
            RETURN d
            """)
        return abs(int(on_off)-1)
    except ClientError as e:
        return int(2)

## Rule Detail Modal
# List Rule Details
def get_rule_details(request, ruleType):
    logType = request['log_type'].split(' ')[0].capitalize()
    rule_name = request['rule_name']
    cypher = f"""
    MATCH (r:Rule:{logType} {{ruleName:'{rule_name}', ruleType:'{ruleType}'}})
    RETURN
        id(r) as id,
        CASE
            WHEN r.ruleClass = 'dynamic' THEN 'Dynamic'
            WHEN r.eventSource IS NULL THEN 'All'
            WHEN r.ruleClass IS NULL OR r.ruleClass = 'static' THEN split(r.eventSource,'.')[0]
            ELSE split(r.eventSource, '.')[0]
        END as type,
        r
    """
    results = graph.run(cypher)
    response = {}
    details = {}
    filter = ['ruleType', 'ruleName', 'ruleComment', 'on_off', 'wheres']
    filter += ['ruleKeys', 'ruleLogicals', 'ruleValues', 'ruleOperators']
    for result in results:
        rule_id = result['id']
        response.update({'id': rule_id})
        response.update({'type': result['type']})
        for key, value in result['r'].items():
            if key == 'query': continue
            if key in filter:
                response.update({key:value})
                continue
            details.update({key.capitalize():value})
    details = dict(sorted(details.items(), key=lambda x: x[0], reverse=False))
    response.update({'details': details})
    response['logType'] = logType
    if response['type'] == 'Dynamic':
        response.update(get_related_flow(logType, rule_name, rule_id))
    return response

# Check And List Related Flow
def get_related_flow(logType, ruleName, rule_id):
    cypher = f"""
        MATCH (rule:Rule:{logType} {{ruleName: '{ruleName}'}})
        WHERE ID(rule) = {rule_id}
        UNWIND KEYS(rule) as key
        WITH DISTINCT(key) as key, rule
        WHERE key =~ 'flow.*'
        WITH rule[key] as flowName
        MATCH (flow:FLOW{{flowName:flowName}})
        RETURN COLLECT(flow) as flows
    """
    results = graph.run(cypher)
    data = []
    filter = ['flowName', 'flowComment']
    for result in results:
        for flow in result['flows']:
            rule = {}
            detail = {}
            for key, value in flow.items():
                if key in filter:
                    rule.update({key:value})
                else:
                    detail.update({key.capitalize():value})
            detail = dict(sorted(detail.items(), key=lambda x: x[0], reverse=False))
            rule.update({'detail': detail})
            data.append(rule)
    response = {'related': data}
    return response