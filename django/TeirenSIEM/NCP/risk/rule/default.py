from django.conf import settings
from py2neo import Graph, ClientError

host = settings.NEO4J_HOST
port = settings.NEO4J_PORT
password = settings.NEO4J_PASSWORD
username = settings.NEO4J_USERNAME
graph = Graph(f"bolt://{host}:{port}", auth=(username, password))

# List All Rules
def get_all_rules():
    global graph
    cypher = f"""
    MATCH (n:RULE:NCP)
    RETURN
        id(n) as id,
        HEAD([label IN labels(n) WHERE label <> 'RULE' AND label <> 'FLOW']) as label,
        CASE
            WHEN 'FLOW' IN labels(n) THEN 'FLOW'
            ELSE n.productName
        END as log_type,
        n.name as name,
        n.comment as comment,
        n.on_off as on_off,
        n.rule_type as rule_type
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
        MATCH (r:RULE:{cloud.upper()} {{rule_type: 'default'}})
        RETURN
        id(r) as id,
        CASE 
            WHEN size(split(r.productName, ',')) > 1 THEN 'FLOW'
            ELSE r.productName
        END as type,
        r.name as name,
        r.comment as comment,
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
        MATCH (r:RULE:{cloud.upper()} {{rule_type: 'custom'}})
        RETURN
        id(r) as id,
        CASE 
            WHEN size(split(r.productName, ',')) > 1 THEN 'FLOW'
            ELSE r.productName
        END as type,
        r.name as name,
        r.comment as comment,
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
    if on_off == '1':
        on_off = 0
    else:
        on_off = 1
    global graph
    cypher = f"""
        MATCH (r:RULE:{cloud} {{name:'{rule_name}'}})
        RETURN r
    """
    node = graph.evaluate(cypher)
    node['on_off'] = int(on_off)
    try:
        graph.push(node)
        return node['on_off']
    except ClientError as e:
        return '실패'

## Rule Detail Modal
# List Rule Details
def get_rule_details(request):
    cloud = request['cloud']
    rule_name = request['rule_name']
    global graph
    cypher = f"""
        MATCH (r:RULE:{cloud} {{name:'{rule_name}'}})
        RETURN
            id(r) as id,
            CASE 
                WHEN size(split(r.productName, ',')) > 1 THEN 'FLOW'
                ELSE r.productName
            END as type,
            r
    """
    results = graph.run(cypher)
    response = {}
    details = {}
    filter = ['rule_type', 'name', 'alert_email1', 'alert_email2', 'comment', 'on_off', 'productName', 'is_allow', 'rule_id']
    for result in results:
        response.update({'id': result['id']})
        response.update({'type': result['type']})
        for key, value in result['r'].items():
            if key in filter:
                response.update({key:value})
                continue
            details.update({key.capitalize():value})
    details = dict(sorted(details.items(), key=lambda x: x[0], reverse=False))
    response.update({'details': details})
    response['cloud'] = cloud
    if response['type'] != 'FLOW':
        response.update(get_related_flow_rule(cloud, rule_name))
    return response

# Check And List Related Flow Rule
def get_related_flow_rule(cloud,rule_name):
    global graph
    cypher = f"""
        MATCH (f:FLOW:{cloud})
        WITH keys(f) as keys, f
        UNWIND keys as key
        WITH f, key where key=~'rule.*' and key <> 'rule_type'
        WITH f where f[key]='{rule_name}'
        RETURN f, id(f) as id
    """
    results = graph.run(cypher)
    data = []
    filter = ['rule_type', 'name', 'comment', 'alert_email1', 'alert_email2', 'on_off', 'productName', 'is_allow']
    for result in results:
        rule = {}
        detail = {}
        rule.update({'id': result['id']})
        for key, value in result['f'].items():
            if key in filter:
                rule.update({key:value})
            else:
                detail.update({key.capitalize():value})
        detail = dict(sorted(detail.items(), key=lambda x: x[0], reverse=False))
        rule.update({'detail': detail})
        data.append(rule)
    response = {'related': data}
    return response