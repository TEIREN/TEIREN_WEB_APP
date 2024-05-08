from django.shortcuts import HttpResponse
from django.conf import settings
from py2neo import Graph
from M_threatD.src.notification.detection import get_relation_json, get_node_json
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


# 사용자별 위협 분석
def get_user_visuals():
    cypher = f"""
    MATCH p = (r:Rule)<-[d:DETECTED|FLOW_DETECTED]-(l:Log)<-[:ACTED|DATE*]-(a:Account)
    WITH DISTINCT(a), count(d) as count, COLLECT(r)[-1] as rule, COLLECT(l)[-1] as log
    RETURN
        HEAD([label IN LABELS(rule) WHERE label <> 'Rule']) AS logType,
        CASE
            WHEN a.userName IS NOT NULL THEN a.userName
            WHEN a.name CONTAINS 'cgid' THEN SPLIT(a.name, '_')[0]
            ELSE a.name
        END AS account,
        CASE
            WHEN a.name CONTAINS 'cgid' THEN a.name
            ELSE '-'
        END AS account_real,
        count AS total,
        rule.ruleName AS recent_detection,
        log.eventName AS recent_action,
        apoc.date.format(apoc.date.parse(log.eventTime, "ms", "yyyy-MM-dd'T'HH:mm:ssX"), "ms", "yyyy-MM-dd HH:mm:ss") AS recent_time
    ORDER BY total DESC
    """
    results = graph.run(cypher)
    response = []
    for result in results:
        response.append(dict(result.items()))
    return response

# 사용자 중심 분석 그래프 시각화
def user_graph(request):
    if type(request) == dict:
        data = get_user_static_data(request)
        data += get_user_dynamic_data(request)
        table = get_user_table(request)
        context = {'graph': json.dumps(data), 'table': table }
        return context
    return HttpResponse('다시 시도')

def get_user_static_data(request):
    account = request['account']
    logType = request['logType']
    cypher = f"""
    MATCH (account:Account)-[:DATE|ACTED*]->(log:Log)-[detected:DETECTED]->(rule:Rule:{logType})
    WHERE account.name = '{account}' or account.userName = '{account}'
    WITH rule, account, detected, log
    MATCH (log)<-[:ACTED*]-(date:Date)<-[date_rel:DATE]-(account)
    WITH log,date,
        [rule, account] as nodes, [detected, date_rel] as relations
    OPTIONAL MATCH (log)<-[:ACTED*]-(mid:Log)
    WITH nodes, relations, log, date, COLLECT(mid) as mid_c
    CALL apoc.do.when(
        SIZE(mid_c) < 1,
        "
            MATCH (log)<-[acted:ACTED]-(date)
            RETURN [log, date] as nodes, [acted] as relations
        ",
        "
            WITH log, date, mid_c
            UNWIND mid_c as mid
            WITH log, date, mid.eventName as eventName, count(mid) as cnt
            WITH log, date, SUM(cnt) AS total, apoc.map.fromPairs(COLLECT([eventName, cnt])) as prop
            CALL apoc.create.vNode(['Between'], apoc.map.merge(prop,{{name:total}})) YIELD node AS analysis
            CALL apoc.create.vRelationship(date,'BETWEEN',{{}}, analysis) YIELD rel AS analyze1
            CALL apoc.create.vRelationship(analysis,'BETWEEN',{{}}, log) YIELD rel AS analyze2
            RETURN [log, date, analysis] as nodes, [analyze1, analyze2] as relations
        ",
        {{log:log, date:date, mid_c:mid_c}}
    ) YIELD value
    WITH nodes + value.nodes as nodes, relations + value.relations as relations, log
    OPTIONAL MATCH (log)-[assumed:ASSUMED]->(role:Role)
    WITH
        CASE 
            WHEN role IS NULL THEN nodes
            ELSE nodes + [role]
        END AS nodes,
        CASE
            WHEN assumed IS NULL THEN relations
            ELSE relations + [assumed]
        END AS relations
    UNWIND relations as relation
    UNWIND nodes AS node
    WITH COLLECT(DISTINCT(relation)) as relations, COLLECT(DISTINCT(node)) as nodes
    UNWIND relations as relation
    WITH nodes,
        COLLECT([
            PROPERTIES(relation),
            ID(relation),
            ID(STARTNODE(relation)),
            ID(ENDNODE(relation)),
            TYPE(relation)
        ]) AS relations
    return nodes, relations
    """
    results = graph.run(cypher)
    response = []
    for result in results:
        data = dict(result)
        for node in data['nodes']:
            response.append(get_node_json(node, logType))
        for relation in data['relations']:
            response.append(get_relation_json(relation))
    return response

def get_user_dynamic_data(request):
    account = request['account']
    logType = request['logType']
    cypher = f"""
    MATCH (account:Account)-[:DATE|ACTED*]->(log:Log)-[detected:FLOW_DETECTED]->(rule:Rule:{logType})
    WHERE account.name = '{account}' OR account.userName = '{account}'
    WITH [rule, account] AS nodes, detected, log, account
    OPTIONAL MATCH (log)-[assumed:ASSUMED]->(role:Role)
    WITH log, detected.path AS path, account,
        CASE
            WHEN role IS NULL THEN nodes
            ELSE nodes + [role]
        END AS nodes,
        CASE
            WHEN assumed IS NULL THEN [detected]
            ELSE [detected, assumed]
        END AS relations
    OPTIONAL MATCH (check:Flow)<-[check_rel:CHECK {{path:path}}]-(log)
    WITH log, path, nodes, relations, check, check_rel, account
    OPTIONAL MATCH (log)<-[flow_rels:FLOW* {{path: path}}]-(flow)
    WHERE flow.userIdentity_arn = log.userIdentity_arn OR log.userName = log.userName
    WITH nodes, log, relations, flow, flow_rels[-1] AS flow_rel, check, check_rel, path, account
    OPTIONAL MATCH (flow)-[check_rels:CHECK {{path: path}}]->(checks:Flow)
    WITH nodes, relations, check, check_rel, flow_rel, account, log,
        COLLECT(checks) AS checks,
        COLLECT(check_rels) AS check_rels,
        COLLECT(flow) AS flow
    WITH nodes + checks + [check] as nodes, relations + check_rels + [check_rel, flow_rel] AS relations, flow, account, log
    WITH nodes + flow AS nodes, relations AS relations, flow[-1] AS last, account, log
    CALL apoc.do.when(
        last IS NULL,
        "
            MATCH (log)<-[:ACTED*]-(date:Date)<-[date_rel:DATE]-(account)
            RETURN [log, account] AS nodes, [date_rel] AS relations, log, date
        ",
        "
            MATCH (last)<-[:ACTED*]-(date:Date)<-[date_rel:DATE]-(account)
            RETURN [log, account] AS nodes, [date_rel] AS relations, last AS log, date
        ",
        {{log:log, last:last, account:account}}
    ) YIELD value
    WITH nodes + value.nodes AS nodes, relations + value.relations AS relations,
        value.log AS log, value.date AS date
    OPTIONAL MATCH (log)<-[:ACTED*]-(mid:Log)
    WITH nodes, relations , log, date, COLLECT(mid) AS mid_c
    CALL apoc.do.when(
        SIZE(mid_c) < 1,
        "
            MATCH (log)<-[acted:ACTED]-(date)
            RETURN [date] AS nodes, [acted] AS relations
        ",
        "
            WITH log, date, mid_c
            UNWIND mid_c AS mid
            WITH log, date, mid.eventName AS eventName, COUNT(mid) AS cnt
            WITH log, date, SUM(cnt) AS total, apoc.map.fromPairs(COLLECT([eventName, cnt])) AS prop
            CALL apoc.create.vNode(['Between'], apoc.map.merge(prop,{{name:total}})) YIELD node AS analysis
            CALL apoc.create.vRelationship(date,'BETWEEN',{{}}, analysis) YIELD rel AS analyze1
            CALL apoc.create.vRelationship(analysis,'BETWEEN',{{}}, log) YIELD rel AS analyze2
            RETURN [date, analysis] AS nodes, [analyze1, analyze2] as relations
        ",
        {{log:log, mid_c:mid_c, date:date}}
    ) YIELD value
    WITH nodes + value.nodes AS nodes, relations + value.relations AS relations
    UNWIND nodes AS node
    UNWIND relations AS relation
    WITH COLLECT(DISTINCT(node)) AS nodes, COLLECT(DISTINCT(relation)) AS relations
    UNWIND relations AS relation
    WITH nodes,
        COLLECT([
            PROPERTIES(relation),
            ID(relation),
            ID(STARTNODE(relation)),
            ID(ENDNODE(relation)),
            TYPE(relation)
        ]) AS relations
    RETURN nodes, relations
    """
    results = graph.run(cypher)
    response = []
    for result in results:
        data = dict(result)
        for node in data['nodes']:
            response.append(get_node_json(node, logType))
        for relation in data['relations']:
            response.append(get_relation_json(relation))
    return response

def get_user_table(request):
    account = request['account']
    cypher = f"""
    MATCH p=(r:Rule)<-[d:DETECTED|FLOW_DETECTED]-(l:Log)<-[:ACTED|DATE*]-(a:Account)
    WHERE a.name = '{account}' or a.userName = '{account}'
    RETURN
        DISTINCT(ID(d)) AS id,
        r.ruleName AS detected_rule,
        l.eventTime AS eventTime,
        apoc.date.format(apoc.date.parse(l.eventTime, "ms", "yyyy-MM-dd'T'HH:mm:ssX"), "ms", "yyyy-MM-dd HH:mm:ss") AS detected_time,
        r.ruleClass AS rule_class,
        [label IN LABELS(r) WHERE label <> 'Rule'][0] AS logType,
        CASE
            WHEN r.level = 1 THEN ['LOW', 'success']
            WHEN r.level = 2 THEN ['MID', 'warning']
            WHEN r.level = 3 THEN ['HIGH', 'caution']
            ELSE ['CRITICAL', 'danger']
        END AS level
    ORDER BY detected_time DESC
    """
    results = graph.run(cypher).data()
    response = []
    for result in results:
        node = dict(result.items())
        arr = {'account': account}
        arr.update(node)
        node.update({'arr': json.dumps(arr)})
        response.append(node)
    return response