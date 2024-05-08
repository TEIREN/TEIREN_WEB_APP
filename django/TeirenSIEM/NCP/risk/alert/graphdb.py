from django.shortcuts import render, redirect, HttpResponse
from django.http import JsonResponse
from django.conf import settings
from py2neo import Graph, NodeMatcher, ClientError
import json
from datetime import datetime
from django.utils import timezone

host = settings.NEO4J_HOST
port = settings.NEO4J_PORT
password = settings.NEO4J_PASSWORD
username = settings.NEO4J_USERNAME
graph = Graph(f"bolt://{host}:{port}", auth=(username, password))


# Node cytoscape.js 형태로 만들기
def get_node_json(node, cloud):
    data = {
        "id" : node.identity,
        "name" : "",
        "score" : 400,
        "query" : True,
        "gene" : True
    }
    property = dict(node.items())
    data['label'] =  list(label for label in node.labels if label != cloud and label != 'FLOW')[0]
    if node.has_label('LOG'):
        data['name'] = property['actionDisplayName'] if 'actionDisplayName' in property else property['name'].split(':')[0]
        data['historyId'] = property['historyId']
        data['eventTime'] = datetime.fromtimestamp(property['eventTime']/1000 + 9*3600, timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        data['actionResultType'] = property['actionResultType']
        data['productName'] = property['productName']
        data['resourceType'] = property['resourceType']
        data['regionName'] = property['regionName'] if 'regionName' in property else '-'
        data['platformType'] = property['platformType'] if 'platformType' in property else '-'
        data['actionUserType'] = property['actionUserType']
        data['sourceType'] = property['sourceType']
    else:
        if node.has_label('IP'):
            data['name'] = property['ipAddress']
        if node.has_label('ACCOUNT'):
            data['score'] = 700
        for key, value in property.items():
            if key == 'name':
                value = value.split(':')[0]
            data[key] = value
    response = {
        "data": data,
        "group" : "nodes"
    }
    return response

# Node 내용
def get_node(request):
    detected_rule = request['detected_rule']
    eventTime = request['eventTime']
    cloud = request['cloud']
    global graph
    cypher = f"""
        MATCH(r:RULE:{cloud} {{name:'{detected_rule}'}})<-[:DETECTED|FLOW_DETECTED]-(l:LOG:{cloud} {{eventTime:{eventTime}}})
        MATCH p=(r)<-[]-(l)<-[:ACTED|DETECTED|FLOW|FLOW_DETECTED|CONNECTED|SUCCESS*]-(x)
        UNWIND nodes(p) as node
        RETURN distinct(node)
    """
    results = graph.run(cypher)
    response = []
    for result in results:
        nodes = dict(result.items())
        for node in nodes.values():
            response.append(get_node_json(node, cloud))
    return response

# Relationship cytoscape.js 형태로 만들기
def get_relation_json(relation):
    data = {
        "source" : relation['start'],
        "target" : relation['end'],
        "weight" : 1,
        "group" : "coexp",
        "id" : "e"+str(relation['id']),
        "name": relation['type']
    }
    response = {
        "data" : data,
        "group" : "edges"
    }
    return response

# Relationship 내용
def get_relation(request):
    detected_rule = request['detected_rule']
    eventTime = request['eventTime']
    cloud = request['cloud']
    global graph
    cypher = f"""
        MATCH(r:RULE:{cloud} {{name:'{detected_rule}'}})<-[:DETECTED|FLOW_DETECTED]-(l:LOG:{cloud} {{eventTime:{eventTime}}})
        MATCH p=(r)<-[d:DETECTED|FLOW_DETECTED]-(l)<-[y:ACTED|DETECTED|FLOW|FLOW_DETECTED|CONNECTED|SUCCESS*]-(x)
        UNWIND relationships(p) as rel
        RETURN
            distinct(properties(rel)) as property,
            id(rel) as id,
            id(startNode(rel)) as start,
            id(endNode(rel)) as end,
            type(rel) as type
    """
    results = graph.run(cypher)
    response = []
    for result in results:
        relation = dict(result.items())
        response.append(get_relation_json(relation))
    return response

# 로그 디테일
def get_log_details(request):
    detected_rule = request['detected_rule']
    eventTime = request['eventTime']
    cloud = request['cloud']
    # global graph
    cypher = f"""
        MATCH (r:RULE:{cloud} {{name:'{detected_rule}'}})<-[:DETECTED|FLOW_DETECTED]-(l:LOG:{cloud} {{eventTime:{eventTime}}})
        OPTIONAL MATCH p=(r)<-[]-(l)<-[:ACTED|DETECTED|FLOW|FLOW_DETECTED|CONNECTED|SUCCESS*]-(x)<-[]-(f{{actionDisplayName:'Login'}})
        WITH p, r, l, f
        CALL apoc.do.when(
            p IS NULL,
            "MATCH p=(:RULE:{cloud} {{name:'{detected_rule}'}})<-[:DETECTED|FLOW_DETECTED]-(l:LOG:{cloud} {{eventTime:{eventTime}}}) RETURN p AS p",
            "RETURN [] AS p",
            {{r:r, l:l, f:f}}
        ) YIELD value
        UNWIND 
            CASE 
                WHEN p is null then nodes(value.p)
                ELSE nodes(p)
            END AS nodes
        WITH distinct(nodes) as node, l, r,
            CASE
                WHEN f IS NOT NULL THEN f 
                ELSE r 
            END as f
        WHERE node <> r and node <> f
        WITH DISTINCT(node) as node,
            CASE
                WHEN node = l THEN 'detected'
                ELSE NULL
            END as detected
        OPTIONAL MATCH (node)-[rel:FLOW]-(l)
        WITH DISTINCT(node) as node, detected, count(rel) as rel_count
        RETURN 
            id(node) as id,
            apoc.date.format(node.eventTime,'ms', 'yyyy-MM-dd HH:mm:ss', 'Asia/Seoul') AS eventTime,
            node.productName as productName,
            node.actionDisplayName as actionType,
            node.actionResultType as resultType,
            node.sourceIp as sourceIP,
            CASE
                WHEN detected IS NOT NULL THEN detected
                WHEN rel_count > 0 THEN 'flow'
                ELSE 'normal'
            END as type,
            node.historyId as historyId
    """
    results = graph.run(cypher).data()
    response = []
    for result in results:
        node = dict(result.items())
        node['cloud'] = cloud
        response.append(node)
    return response

# URL /neo4j/
def neo4j_graph(request):
    if isinstance(request, dict) :
        data = get_node(request)
        data += get_relation(request)
        details = get_log_details(request)
        context = {'graph': json.dumps(data), 'details': details }
        return context
    elif request.method == 'POST':
        context = dict(request.POST.items())
        data = get_node(context)
        data += get_relation(context)
        details = get_log_details(context)
        context.update({'graph': json.dumps(data), 'details': details})
        return render(request, 'graphdb/graph.html', context)
    return HttpResponse('다시 시도')

# 위협알림 log
def get_alert_logs():
    global graph
    cypher = '''
        MATCH (l:LOG)-[n:DETECTED|FLOW_DETECTED]->(r:RULE{is_allow:1})
        WHERE n.alert = 1 AND n.alert IS NOT NULL
        RETURN
            head([label IN labels(l) WHERE label <> 'LOG']) AS cloud,
            apoc.date.format(n.detected_time,'ms', 'yyyy-MM-dd HH:mm:ss', 'Asia/Seoul') AS detected_time,
            r.comment as detectedAction,
            l.actionDisplayName as actionDisplayName,
            l.actionResultType as actionResultType,
            l.eventTime as eventTime,
            apoc.date.format(l.eventTime,'ms', 'yyyy-MM-dd HH:mm:ss', 'Asia/Seoul') AS eventTime_format,
            l.sourceIp as sourceIp,
            r.name as detected_rule,
            r.name+'#'+id(n) AS rule_name
        ORDER BY eventTime DESC
    '''
    results = graph.run(cypher)
    data = check_alert_logs()
    filter = ['cloud', 'detected_rule', 'eventTime', 'rule_name']
    for result in results:
        detail = dict(result.items())
        form = {}
        for key in filter:
            if key != 'cloud' and key != 'rule_name':
                value = detail.pop(key)
            else:
                value = detail[key]
            form[key] = value
        detail['form'] = form
        data.append(detail)
    context = {'data': data}
    return context

def check_alert_logs():
    global graph
    cypher = """
    MATCH (r:RULE)<-[n:DETECTED|FLOW_DETECTED]-(l:LOG)
    WHERE
        r.is_allow = 1 AND
        n.alert <> 1
     RETURN
        head([label IN labels(l) WHERE label <> 'LOG']) AS cloud,
        apoc.date.format(n.detected_time,'ms', 'yyyy-MM-dd HH:mm:ss', 'Asia/Seoul') AS detected_time,
        r.comment as detectedAction,
        l.actionDisplayName as actionDisplayName,
        l.actionResultType as actionResultType,
        l.eventTime as eventTime,
        apoc.date.format(l.eventTime,'ms', 'yyyy-MM-dd HH:mm:ss', 'Asia/Seoul') AS eventTime_format,
        l.sourceIp as sourceIp,
        r.name as detected_rule,
        r.name+'#'+id(n) AS rule_name,
        n.alert as alert
    ORDER BY alert, eventTime DESC
    """
    results = graph.run(cypher)
    data = []
    filter = ['cloud', 'detected_rule', 'eventTime', 'rule_name', 'alert']
    for result in results:
        detail = dict(result.items())
        form = {}
        for key in filter:
            if key != 'cloud' and key != 'rule_name' and key != 'alert':
                value = detail.pop(key)
            else:
                value = detail[key]
            form[key] = value
        detail['form'] = form
        data.append(detail)
    return data

# 사용자별 위협 분석
def get_user_visuals():
    global graph
    cypher = f"""
    MATCH (p)<-[:POINTER]-(n:ACCOUNT)-[*]->()-[d:DETECTED|FLOW_DETECTED]->(r:RULE)
    WHERE r.is_allow = 1
    WITH
        p.actionDisplayName as recent_action,
        apoc.date.format(p.eventTime,'ms', 'yyyy-MM-dd HH:mm:ss', 'Asia/Seoul') as recent_time, 
        n.userName AS account,
        count(distinct(d)) AS total,
        HEAD([label IN labels(n) WHERE label <> 'ACCOUNT']) AS cloud,
        HEAD(apoc.coll.sortMulti(COLLECT({{id:id(d), time:d.detected_time}}), ['time'])).id AS detection
    MATCH (r:RULE)<-[d:DETECTED|FLOW_DETECTED]-()
    WHERE id(d) = detection AND cloud <> 'ACCOUNT'
    RETURN 
        cloud, account, total, r.name as recent_detection, recent_action, recent_time
    ORDER BY total DESC
    """
    results = graph.run(cypher)
    response = []
    for result in results:
        response.append(dict(result.items()))
    return response

# 사용자 중심 분석 그래프 시각화
def user_graph(request):
    if isinstance(request, dict) :
        data = get_user_node(request)
        data += get_user_relation(request)
        table = get_user_table(request)
        context = {'graph': json.dumps(data), 'table': table }
        return context
    return HttpResponse('다시 시도')

def get_user_node(request):
    account = request['account']
    cloud = request['cloud']
    global graph
    cypher = f"""
    MATCH p = (a:ACCOUNT{{userName:'{account}'}})-[:ACTED|FLOW|CONNECTED|SUCCESS*]->(l)-[*]->(r:RULE)
    WHERE r.is_allow = 1
    UNWIND NODES(p) as node
    RETURN DISTINCT(node)
    """
    results = graph.run(cypher)
    response = []
    for result in results:
        nodes = dict(result.items())
        for node in nodes.values():
            response.append(get_node_json(node, cloud))
    return response

def get_user_relation(request):
    account = request['account']
    global graph
    cypher = f"""
    MATCH p=(a:ACCOUNT{{userName:'{account}'}})-[y:ACTED|FLOW|CONNECTED|SUCCESS*]->(l)-[d:DETECTED|FLOW_DETECTED*]->(r:RULE)
    WHERE r.is_allow = 1
    UNWIND RELATIONSHIPS(p) as rel
    RETURN
        distinct(properties(rel)) as property,
        id(rel) as id,
        id(startNode(rel)) as start,
        id(endNode(rel)) as end,
        type(rel) as type
    """
    results = graph.run(cypher)
    response = []
    for result in results:
        relation = dict(result.items())
        response.append(get_relation_json(relation))
    return response

def get_user_table(request):
    account = request['account']
    global graph
    cypher = f"""
    MATCH (n:ACCOUNT {{userName:'{account}'}})-[*]->(l)-[d:DETECTED|FLOW_DETECTED]->(r:RULE)
    WHERE r.is_allow = 1
    UNWIND [label IN LABELS(n) WHERE label <> 'ACCOUNT'] AS cloud
    RETURN
    DISTINCT(id(d)) AS id,
    d.name AS detected_rule,
    l.eventTime as eventTime,
    apoc.date.format(d.detected_time,'ms', 'yyyy-MM-dd HH:mm:ss', 'Asia/Seoul') as detected_time,
    CASE
        WHEN 'FLOW' IN LABELS(r) THEN 'FLOW'
        ELSE r.productName
    END AS rule_type,
    cloud
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

# Top Bar 위협 알림
def check_topbar_alert():
    global graph
    cypher = """
    MATCH (r:RULE)<-[n:DETECTED|FLOW_DETECTED]-()
    WHERE r.is_allow = 1 AND (n.alert = 0 OR n.alert IS NULL)
    SET n.alert = CASE
            WHEN n.alert IS NULL THEN 0
            ELSE n.alert
        END
    RETURN COUNT(n) as count
    """
    results = graph.run(cypher)
    for result in results:
        count = result['count']
    if count > 0:
        response = {'top_alert':{'count': count}}
    else:
        response = {'no_top_alert': 1}
    return response

# 위협 알림 확인 후 Alert Off
def alert_off(request):
    if 'alert' in request:
        detected_rule = request['detected_rule']
        cloud = request['cloud']
        eventTime = request['eventTime']
        global graph
        cypher = f"""
        MATCH (r:RULE:{cloud} {{name:'{detected_rule}'}})<-[n:DETECTED|FLOW_DETECTED]-(l:LOG:{cloud} {{eventTime:{eventTime}}})
        WHERE 
            r.is_allow = 1 AND
            n.alert IS NOT NULL AND
            n.alert = 0
        SET n.alert = 1
        RETURN count(n.alert)
        """
        graph.evaluate(cypher)
    return request
