from django.conf import settings
from py2neo import Graph, ClientError
from TeirenSIEM.risk.rule.add import add_static_rule, add_dynamic_rule
from TeirenSIEM.risk.rule.delete import delete_static_rule, delete_dynamic_rule
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

## Edit Rule Modal
# List Edit Rule Details (For Edit Rule Modal)
def get_edit_rule_page(request):
    rule_type = request['rule_type']
    if rule_type == 'Dynamic':
        response = dynamic_edit_rule_page(request)
    else:
        response = static_edit_rule_page(request)
    return response

def static_edit_rule_page(request):
    rule_type = request['rule_type']
    og_rule_name = request['rule_name']
    rule_id = request['rule_id']
    cloud = request['cloud']
    response ={}
    cypher = f"""
    MATCH (rule:Rule:{cloud} {{ruleName:'{og_rule_name}', ruleClass:'static'{f", eventSource:'{rule_type}.amazonaws.com'" if rule_type != 'All' else ""}}})
    WHERE ID(rule) = {rule_id}
    UNWIND KEYS(rule) as key
    WITH key, rule
    WHERE key IN ['ruleKeys', 'ruleValues', 'ruleOperators', 'ruleLogicals']
    WITH DISTINCT(key) as key, rule
    WITH rule, key, COLLECT(rule[key]) AS values
    UNWIND values AS val_list
    UNWIND range(0,size(val_list)-1) AS index
    WITH rule, index, apoc.map.fromPairs(COLLECT([key, val_list[index]])) AS properties
    WITH rule, COLLECT(properties) AS properties
    RETURN
        rule.ruleName as ruleName,
        rule.ruleComment as ruleComment,
        rule.ruleCount as ruleCount,
        rule.timeRange as timeRange,
        rule.level as level,
        CASE rule.level
            WHEN 1 THEN 'LOW'
            WHEN 2 THEN 'MID'
            WHEN 3 THEN 'HIGH'
            ELSE 'CRITICAL' 
        END as level_label,
        properties
    """
    results = graph.run(cypher)
    for result in results:
        static = dict(result)
        break
    response.update({'static': static })
    return response

def dynamic_edit_rule_page(request):
    og_rule_name = request['rule_name']
    rule_id = request['rule_id']
    cloud = request['cloud']
    response ={}
    cypher = f"""
    MATCH (rule:Rule:{cloud} {{ruleName:'{og_rule_name}', ruleClass:'dynamic'}})
    WHERE ID(rule) = {rule_id}
    UNWIND KEYS(rule) as keys
    WITH rule, keys
    WHERE keys =~ 'flow.*'
    WITH rule, keys ORDER BY keys
    WITH rule, rule[keys] as flowName
    MATCH (flow:Flow{{flowName:flowName}})
    WITH rule, flow
    UNWIND KEYS(flow) as key 
    WITH rule, flow, key
    WHERE NOT key IN ['flowName', 'flowComment', 'count']
    WITH rule, flow, COLLECT(key) as keys
    WITH rule, flow, keys, [key IN keys | flow[key]] AS vals
    WITH rule, {{flowName:flow.flowName, flowComment:flow.flowComment, keys: keys, values:vals}} as flows, flow
    WITH rule,
        CASE
            WHEN flow.count IS NULL THEN flows
            ELSE apoc.map.merge(flows, {{count:flow.count}})
        END AS flows
    RETURN
        rule.ruleName as ruleName,
        rule.ruleComment as ruleComment,
        rule.timeRange as timeRange,
        rule.wheres as wheres,
        rule.level as level,
        CASE rule.level
            WHEN 1 THEN 'LOW'
            WHEN 2 THEN 'MID'
            WHEN 3 THEN 'HIGH'
            ELSE 'CRITICAL'
        END as level_label,
        COLLECT(flows) as flows
    """
    results = graph.run(cypher)
    for result in results:
        dynamic = dict(result)
        dynamic['wheres'] = json.dumps([parse_dict(s) for s in dynamic.pop('wheres')])
        break
    response.update({'dynamic': dynamic })
    return response

def parse_dict(s):
    s = s.strip('{}')
    items = s.split(', ')
    d = {}
    for item in items:
        key_value = item.split(':')
        d[key_value[0]] = key_value[1]
    return d

# Edit Rule Action
def edit_rule(request):
    if request['ruleClass'] == 'static':
        return edit_static_rule(request)
    else:
        return edit_dynamic_rule(request)

def edit_static_rule(request):
    request['count'] = 1
    ruleName = request['ruleName']
    og_ruleName = request['og_rule_name']
    cloud = request['cloud']
    if ruleName != og_ruleName and graph.evaluate(f"""
    MATCH (rule:Rule:{cloud} {{ruleName: '{ruleName}'}})
    RETURN COUNT(rule)
    """) > 0:
        return f"'{ruleName}'이라는 이름의 정책이 이미 존재합니다. 다른 이름으로 정책을 설정해주세요."
    request['check'] = 1
    if isinstance(add_check:=add_static_rule(request), str):
        return add_check
    if isinstance(delete_check:=delete_static_rule(request), str):
        return delete_check
    result = add_static_rule(request)
    return result

def edit_dynamic_rule(request):
    ruleName = request['ruleName']
    og_ruleName = request['og_rule_name']
    cloud = request['cloud']
    if ruleName != og_ruleName and graph.evaluate(f"""
    MATCH (rule:Rule:{cloud} {{ruleName: '{ruleName}'}})
    RETURN COUNT(rule)
    """) > 0:
        return f"'{ruleName}'이라는 이름의 정책이 이미 존재합니다. 다른 이름으로 정책을 설정해주세요."
    request['check'] = 1
    if isinstance(add_check:=add_dynamic_rule(request), str):
        return add_check
    if isinstance(delete_check:=delete_dynamic_rule(request), str):
        return delete_check
    result = add_dynamic_rule(request)
    return result

# Change Epoch To Time
def timerange_to_timedict(timerange):
    time = int(timerange / 1000)
    seconds = int(time)
    minutes = int(seconds/60)
    hours = int(minutes/60)
    days = int(hours/24)
    seconds = int(seconds % 60)
    minutes = int(minutes % 60)
    hours = int(hours % 24)
    response = {
        'seconds': seconds,
        'minutes': minutes,
        'hours': hours,
        'days': days
    }
    return response

# Change Time to Epoch
def timedict_to_timerange(time):
    days = int(time['days']) if 'days' in time else 0
    hours = int(time['hours']) if 'hours' in time else 0
    minutes = int(time['minutes']) if 'minutes' in time else 0
    seconds = int(time['seconds']) if 'seconds' in time else 0
    days *= 86400
    hours *= 3600
    minutes*= 60
    result = days+hours+minutes+seconds
    result *= 1000
    response = result
    return response