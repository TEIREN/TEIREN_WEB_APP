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
    global graph
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
        r.on_off as on_off,
        r.ruleType as rule_type
    """
    results = graph.run(cypher)
    data = []
    for result in results:
        data.append(dict(result))
    response = {'rules': data}
    return response

# List Default Rules
def get_default_rules(cloud):
    global graph
    cypher= f"""
    MATCH (r:Rule:{cloud.capitalize()} {{ruleType: 'default'}})
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
    r.on_off as on_off
    """
    results = graph.run(cypher)
    data = []
    for result in results:
        data.append(dict(result.items()))
    response = {'default': data}
    return response

# List Custom Rules
def get_custom_rules(cloud):
    global graph
    cypher= f"""
    MATCH (r:Rule:{cloud.capitalize()} {{ruleType: 'custom'}})
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
    r.on_off as on_off
    """
    results = graph.run(cypher)
    data = []
    for result in results:
        data.append(dict(result.items()))
    response = {'custom': data}
    return response

# Rule On Off
def rule_on_off(request):
    cloud = request['cloud']
    rule_name = request['rule_name']
    on_off = request['on_off']
    cypher = f"""
    MATCH (r:Rule:{cloud} {{ruleName:'{rule_name}'}})
    SET r.on_off = {abs(int(on_off)-1)}
    RETURN r
    """
    try:
        graph.evaluate(cypher)
        return abs(int(on_off)-1)
    except ClientError as e:
        return '실패'

## Rule Detail Modal
# List Rule Details
def get_rule_details(request, type):
    cloud = request['cloud']
    rule_name = request['rule_name']
    global graph
    cypher = f"""
    MATCH (r:Rule:{cloud} {{ruleName:'{rule_name}', ruleType:'{type}'}})
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
    response['cloud'] = cloud
    if response['type'] == 'Dynamic':
        response.update(get_related_flow(cloud, rule_name, rule_id))
    return response

# Check And List Related Flow
def get_related_flow(cloud, ruleName, rule_id):
    global graph
    cypher = f"""
        MATCH (rule:Rule:{cloud} {{ruleName: '{ruleName}'}})
        WHERE ID(rule) = {rule_id}
        UNWIND KEYS(rule) as key
        WITH DISTINCT(key) as key, rule
        WHERE key =~ 'flow.*'
        WITH rule[key] as flowName
        MATCH (flow:FLOW_TEST{{flowName:flowName}})
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