from django.conf import settings
from django.shortcuts import render, HttpResponse
from py2neo import Graph
from webAPP.django.TeirenSIEM.v1.graphdb import neo4j_graph as ncp
import json, operator

## AWS
host = settings.NEO4J['HOST']
port = settings.NEO4J["PORT"]
username = settings.NEO4J['USERNAME']
password = settings.NEO4J['PASSWORD']
graph = Graph(f"bolt://{host}:{port}", auth=(username, password))

def neo4j_graph(request):
    if isinstance(request, dict) :
        if request['cloud'] == 'NCP':
            context = ncp(request)
            return context
        data = get_data(request)
        details = get_log_details(request)
        context = {'graph': json.dumps(data), 'details': details }
        return context
    elif request.method == 'POST':
        context = dict(request.POST.items())
        if context['cloud'] == 'NCP':
            context = ncp(request)
            return context
        data = get_data(context)
        details = get_log_details(context)
        context.update({'graph': json.dumps(data), 'details': details})
        return render(request, 'graphdb/graph.html', context)
    return HttpResponse('다시 시도')


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
    property = {key:property[key] for key in sorted(property.keys())}
    if node.has_label('Log'):
        data['label'] = 'Log'
        for key, value in property.items():
            if key == 'eventName':
                data['name'] = value
            else:
                if 'responseElements' in key or 'requestParameters' in key or 'tls' in key:
                    continue
                if 'userAgent' in key:
                    continue
                if 'errorMessage' in key:
                    value = value.replace('\'', '[',1)
                    value = value.replace('\'', ']',1)
                if '\'' in str(value):
                    value = value.replace('\'', '[',1)
                    value = value.replace('\'', ']',1)
                data[key] = value
    else:
        if node.has_label('Flow'):
            data['label'] = 'Flow'
            data['name'] = property['flowName']
        if node.has_label('Date'):
            data['label'] = 'Date'
        if node.has_label('Account'):
            data['label'] = 'Account'
            data['score'] = 700
        if node.has_label('Between'):
            data['label'] = 'Between'
            property = dict(sorted(property.items(), key=operator.itemgetter(1), reverse=True))
        if node.has_label('Role'):
            data['label'] = 'Role'
        if node.has_label('Rule'):
            data['label'] = 'Rule'
            data['name'] = property['ruleName']
        for key, value in property.items():
            if key == 'name':
                value = str(value)
                value = value.split('_')[0]
            if 'responseElements' in key or 'requestParameters' in key or 'tls' in key:
                continue
            if 'errorMessage' in key:
                value = value.replace('\'', '[',1)
                value = value.replace('\'', ']',1)
            if key == 'date':
                value = str(value)
                data['name'] = value
            data[key] = value
    response = {
        "data": data,
        "group" : "nodes"
    }
    return response


def get_data(request):
    rule_type = request['rule_type']
    if rule_type == 'default':
        data = get_default(request)
    else:
        data = get_flow(request)
    return data

def get_log_details(request):
    rule_type = request['rule_type']
    if rule_type == 'default':
        details = get_default_details(request)
    else:
        details = get_flow_details(request)
    return details

# Default Rule
def get_default(request):
    detected_rule = request['detected_rule']
    eventTime = request['eventTime']
    cloud = request['cloud']
    id = request['id']
    cypher = f"""
    MATCH (rule:Rule:{cloud}{{ruleName: '{detected_rule}'}})<-[detect:DETECTED]-(log:Log:{cloud}{{eventTime:'{eventTime}'}})
    WHERE ID(detect) = {id}
    WITH rule, detect, log
    OPTIONAL MATCH p=(log)<-[:ACTED*6]-(:Log)
    CALL apoc.do.when(
        p IS NULL,
        "
            MATCH p=(log)<-[:ACTED|DATE*]-(:Account)
            WITH COLLECT(p)[-1] as p
            WITH NODES(p) as nodes, RELATIONSHIPS(p) as relations
            RETURN nodes, relations
            ",
        "
            MATCH p=(log)<-[:ACTED*..5]-(view:Log)
            WITH COLLECT(p)[-1] as p
            WITH NODES(p) as nodes, RELATIONSHIPS(p) as relations
            WITH nodes, relations, nodes[-1] as last
            MATCH (last)<-[:ACTED*]-(date:Date)<-[date_rel:DATE]-(account:Account)
            WITH nodes + [account] as nodes, relations + [date_rel] as relations, date, last
            MATCH (last)<-[:ACTED*]-(mid:Log)
            WITH mid.eventName as eventName, COUNT(mid) as cnt, last, date, nodes, relations
            WITH apoc.map.fromPairs(COLLECT([eventName, cnt])) as prop, nodes, relations, date, last, SUM(cnt) as total
            CALL apoc.create.vNode(['Between'], apoc.map.merge(prop,{{name: total}})) YIELD node AS analysis
            CALL apoc.create.vRelationship(date,'BETWEEN',{{}}, analysis) YIELD rel AS analyze1
            CALL apoc.create.vRelationship(analysis,'BETWEEN',{{}}, last) YIELD rel AS analyze2
            WITH nodes + [date,analysis] as nodes, relations + [analyze1,analyze2] as relations
            RETURN nodes, relations
        ",
        {{log:log}}
    ) YIELD value
    WITH value.nodes + [rule] as nodes, value.relations + [detect] as relations, log
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
    WITH nodes,
        [
            PROPERTIES(relation),
            ID(relation),
            ID(STARTNODE(relation)),
            ID(ENDNODE(relation)),
            TYPE(relation)
        ] AS relation
    RETURN nodes, COLLECT(relation) as relations
    """
    results = graph.run(cypher)
    response = []
    for result in results:
        data = dict(result)
        for node in data['nodes']:
            response.append(get_node_json(node, cloud))
        for relation in data['relations']:
            response.append(get_relation_json(relation))
    return response

# Flow Rule
def get_flow(request):
    detected_rule = request['detected_rule']
    eventTime = request['eventTime']
    cloud = request['cloud']
    id = request['id']
    cypher = f"""
    MATCH (rule:Rule:{cloud}{{ruleName:'{detected_rule}'}})<-[detected:FLOW_DETECTED]-(log:Log:{cloud}{{eventTime:'{eventTime}'}})-[check_rel:CHECK]->(check:Flow)
    WHERE ID(detected) = {id} AND check_rel.path = detected.path
    WITH log, detected, rule, check_rel, check
    MATCH p=(log)<-[flow_rel:FLOW* {{path: detected.path}}]-(flow)-[check_rels:CHECK]->(checks:Flow)
    WITH COLLECT(flow_rel[-1]) as flow_rel, COLLECT(flow) as flows, log, rule, detected,check, check_rel,detected.path as path,
        COLLECT(checks) AS checks,
        COLLECT(check_rels) AS check_rels
    OPTIONAL MATCH (log)-[assumed:ASSUMED]->(role:Role)
    WITH flows, path, log,
        CASE
            WHEN role IS NULL THEN [rule, check] + checks
            ELSE [rule, check, role] + checks
        END AS nodes,
        CASE
            WHEN assumed IS NULL THEN [detected, check_rel] + check_rels + flow_rel
            ELSE [detected, check_rel, assumed] + check_rels + flow_rel
        END AS relations
    UNWIND flows as flow
    OPTIONAL MATCH (flow)<-[:FLOW {{path:path}}]-(flow2)
    WITH log, nodes, relations, path, flow, flow2,
        CASE 
            WHEN flow2 IS NULL THEN 'diff'
            WHEN flow.userIdentity_arn <> flow2.userIdentity_arn THEN 'diff'
            WHEN flow.userIdentity_type = flow2.userIdentity_type THEN 'same'
            WHEN flow.userIdentity_type <> flow.userIdentity_type THEN 'diff'
            ELSE 'same'
        END AS flow_check
    CALL apoc.do.when(
        flow_check = 'diff',
        "
            MATCH (flow)-[:FLOW {{path:path}}]->(flow2)
            WITH flow, flow2, path,
                CASE
                    WHEN flow.userIdentity_arn <> flow2.userIdentity_arn THEN 'diff'
                    WHEN flow.userIdentity_arn = flow2.userIdentity_arn THEN 'same'
                    WHEN flow.userIdentity_type = flow2.userIdentity_type THEN 'same'
                    WHEN flow.userIdentity_type <> flow2.userIdentity_type THEN 'diff'
                    ELSE 'diff'
                END AS flow_check
            CALL apoc.do.when(
                flow_check = 'same',
                \\\"
                    MATCH (flow)<-[:ACTED*]-(date:Date)<-[date_rel:DATE]-(account:Account)
                    WITH flow, date, date_rel, account, flow2
                    MATCH (flow)<-[:ACTED*]-(mid:Log)
                    WITH flow, date, date_rel, account, mid.eventName as eventName, COUNT(mid) as cnt, flow2
                    WITH flow, date, date_rel, account, SUM(cnt) as total, flow2,
                        apoc.map.fromPairs(COLLECT([eventName,cnt])) as prop
                    CALL apoc.create.vNode(['Between'], apoc.map.merge(prop,{{name:total}})) YIELD node AS analysis
                    CALL apoc.create.vRelationship(date,'BETWEEN',{{}}, analysis) YIELD rel AS analyze1
                    CALL apoc.create.vRelationship(analysis,'BETWEEN',{{}}, flow) YIELD rel AS analyze2
                    WITH flow, flow2, [date, analysis, account] as nodes, [date_rel, analyze1, analyze2] as relations
                    OPTIONAL MATCH (flow)-[assumed:ASSUMED]->(role:Role)
                    WITH flow, flow2,
                        CASE
                            WHEN role IS NULL THEN nodes
                            ELSE nodes + [role]
                        END AS nodes,
                        CASE
                            WHEN assumed IS NULL THEN relations
                            ELSE relations + [assumed]
                        END AS relations
                    OPTIONAL MATCH p=(flow)-[:ACTED|NEXT*]->(flow2)
                    WITH flow, flow2, nodes, relations, NODES(p) as mid
                    CALL apoc.do.when(
                        SIZE(mid) <= 2,
                        \\\\\\"
                            MATCH (flow)-[acted:ACTED]->(flow2)
                            RETURN [flow] as nodes, [acted] as relations
                        \\\\\\",
                        \\\\\\"
                            MATCH p=(flow)-[:ACTED|NEXT*]->(flow2)
                            WITH flow, flow2, NODES(p) as mids
                            UNWIND mids as mid
                            WITH flow, flow2, mid
                            WHERE ID(mid)<>ID(flow) AND ID(mid) <> ID(flow2)
                            WITH flow, flow2, mid.eventName as eventName, COUNT(mid) as cnt
                            WITH flow, flow2, SUM(cnt) as total,
                                apoc.map.fromPairs(COLLECT([eventName,cnt])) as prop
                            CALL apoc.create.vNode(['Between'], apoc.map.merge(prop,{{name: total}})) YIELD node AS analysis
                            CALL apoc.create.vRelationship(flow,'BETWEEN',{{}}, analysis) YIELD rel AS analyze1
                            CALL apoc.create.vRelationship(analysis,'BETWEEN',{{}}, flow2) YIELD rel AS analyze2
                            RETURN [flow, analysis] as nodes, [analyze1, analyze2] as relations
                        \\\\\\",
                        {{flow:flow, flow2:flow2}}
                    ) YIELD value
                    WITH value.nodes + nodes as nodes, value.relations + relations as relations
                    RETURN nodes, relations
                \\\",
                \\\"
                    MATCH (flow)<-[:ACTED*]-(date:Date)<-[date_rel:DATE]-(account:Account)
                    WITH flow, date, date_rel, account
                    OPTIONAL MATCH (flow)<-[:ACTED*]-(mid:Log)
                    WITH flow, date, date_rel, account, COLLECT(mid) as mid
                    CALL apoc.do.when(
                        SIZE(mid) = 0 ,
                        \\\\\\"
                            MATCH (flow)<-[acted:ACTED]-(date)
                            RETURN [flow, date] as nodes, [acted] as relations
                        \\\\\\",
                        \\\\\\"
                            MATCH (flow)<-[:ACTED*]-(mid:Log)
                            WITH flow, date, mid.eventName as eventName, COUNT(mid) as cnt
                            WITH flow, date, SUM(cnt) as total,
                                apoc.map.fromPairs(COLLECT([eventName,cnt])) as prop
                            CALL apoc.create.vNode(['Between'], apoc.map.merge(prop,{{name: total}})) YIELD node AS analysis
                            CALL apoc.create.vRelationship(date,'BETWEEN',{{}}, analysis) YIELD rel AS analyze1
                            CALL apoc.create.vRelationship(analysis,'BETWEEN',{{}}, flow) YIELD rel AS analyze2
                            RETURN [flow, date, analysis] as nodes, [analyze1, analyze2] as relations
                        \\\\\\",
                        {{flow: flow, date:date}}
                    )YIELD value
                    WITH value.nodes + [account] as nodes, value.relations + [date_rel] as relations, flow
                    OPTIONAL MATCH (flow)-[view_rel:ACTED*..5]->(view:Log)
                    WITH nodes, relations, COLLECT(view) as view, COLLECT(view_rel[-1]) as view_rel, flow
                    WITH nodes + view as nodes, relations + view_rel as relations, flow
                    OPTIONAL MATCH (flow)-[assumed:ASSUMED]->(role:Role)
                    WITH
                        CASE
                            WHEN role IS NULL THEN nodes
                            ELSE nodes + [role]
                        END AS nodes,
                        CASE
                            WHEN assumed IS NULL THEN relations
                            ELSE relations + [assumed]
                        END AS relations
                    RETURN nodes, relations
                \\\",
                {{flow:flow, flow2:flow2}}
            ) YIELD value
            RETURN value
        ",
        "
            MATCH (flow)-[:FLOW{{path:path}}]->(flow2)
            WITH flow, flow2,
                CASE
                    WHEN flow.userIdentity_arn IS NULL AND flow2.userIdentity_arn IS NULL THEN 'same'
                    WHEN flow.userIdentity_arn = flow2.userIdentity_arn THEN 'same'
                    WHEN flow.userIdentity_type = flow2.userIdentity_type THEN 'same'
                    WHEN flow.userIdentity_type <> flow2.userIdentity_type THEN 'diff'
                    ELSE 'diff'
                END AS flow_check
            CALL apoc.do.when(
                flow_check = 'same',
                \\\"
                    MATCH p=(flow)-[:ACTED|NEXT*]->(flow2)
                    WITH flow, flow2, NODES(p) as mids
                    UNWIND mids as mid
                    WITH flow, flow2, mid
                    WHERE ID(mid) <> ID(flow) AND ID(mid) <> ID(flow2)
                    WITH mid.eventName as eventName, COUNT(mid) as cnt, flow, flow2
                    WITH flow, flow2, SUM(cnt) as total, apoc.map.fromPairs(COLLECT([eventName,cnt])) as prop
                    CALL apoc.create.vNode(['Between'], apoc.map.merge(prop,{{name:total}})) YIELD node AS analysis
                    CALL apoc.create.vRelationship(flow,'BETWEEN',{{}}, analysis) YIELD rel AS analyze1
                    CALL apoc.create.vRelationship(analysis,'BETWEEN',{{}}, flow2) YIELD rel AS analyze2
                    WITH flow, analysis, [analyze1, analyze2] AS relations
                    OPTIONAL MATCH (flow)-[assumed:ASSUMED]->(role:Role)
                    WITH
                        CASE
                            WHEN role IS NULL THEN [flow, analysis]
                            ELSE [flow, analysis, role]
                        END AS nodes,
                        CASE
                            WHEN assumed IS NULL THEN relations
                            ELSE relations + [assumed]
                        END AS relations
                    RETURN nodes, relations
                \\\",
                \\\"
                    OPTIONAL MATCH (flow)-[view_rels:ACTED*..5]->(view:Log)
                    WITH flow, COLLECT(view_rels[-1]) as view_rels, COLLECT(view) as view
                    OPTIONAL MATCH (flow)-[assumed:ASSUMED]->(role:Role)
                    WITH
                        CASE
                            WHEN role IS NULL THEN view + [flow]
                            ELSE view + [flow, role]
                        END AS nodes,
                        CASE
                            WHEN assumed IS NULL THEN view_rels
                            ELSE view_rels + [assumed]
                        END AS relations
                    RETURN nodes, relations
                \\\",
                {{flow:flow, flow2:flow2}}
            ) YIELD value
            RETURN value
        ",
        {{flow:flow, path:path}}
    ) YIELD value
    UNWIND value.value.relations as relation
    UNWIND value.value.nodes as node
    WITH relations, nodes, log, path,
        COLLECT(DISTINCT(node)) as nodes2,
        COLLECT(DISTINCT(relation)) as relations2
    WITH nodes + nodes2 as nodes, relations + relations2 as relations, log, path
    MATCH (log)<-[:FLOW {{path:path}}]-(flow)
    WITH log, nodes, relations,
        CASE
            WHEN log.userIdentity_arn <> flow.userIdentity_arn THEN 'diff'
            WHEN log.userIdentity_arn = flow.userIdentity_arn THEN 'same'
            WHEN log.userIdentity_type = flow.userIdentity_type THEN 'same'
            WHEN log.userIdentity_type <> flow.userIdentity_type THEN 'diff'
            ELSE 'diff'
        END AS flow_check
    CALL apoc.do.when(
        flow_check = 'diff',
        "
            MATCH (log)<-[:ACTED*]-(date:Date)<-[date_rel:DATE]-(account:Account)
            WITH log, date, account, date_rel
            OPTIONAL MATCH (log)<-[:ACTED*]-(mid:Log)
            WITH log, date, account, date_rel, COLLECT(mid) as mid
            CALL.apoc.do.when(
                SIZE(mid) = 0,
                \\\"
                    MATCH (log)<-[acted:acted]-(date)
                    RETURN [log, date, account] as nodes, [acted, date_rel] as relations
                \\\",
                \\\"
                    MATCH (log)<-[:ACTED*]-(mid:Log)
                    WITH log, date, account, date_rel, mid.eventName as eventName, COUNT(mid) as cnt
                    WITH log, date, account, date_rel, SUM(cnt) as total,
                        apoc.map.fromPairs(COLLECT([eventName,cnt])) as prop
                    CALL apoc.create.vNode(['Between'], apoc.map.merge(prop,{{name:'Analysis', total: total}})) YIELD node AS analysis
                    CALL apoc.create.vRelationship(date,'BETWEEN',{{}}, analysis) YIELD rel AS analyze1
                    CALL apoc.create.vRelationship(analysis,'BETWEEN',{{}}, log) YIELD rel AS analyze2
                    RETURN [log, date, account, analysis] as nodes, [analyze1, analyze2, date_rel] as relations
                \\\",
                {{log:log, date:date, date_rel:date_rel, account:account}}
            ) YIELD value
            RETURN value
        ",
        "   
            WITH {{nodes: [log], relations:[]}} as value
            RETURN value
        ",
        {{log:log}}
    ) YIELD value
    WITH nodes + value.value.nodes as nodes, relations + value.value.relations as relations
    UNWIND relations as relation
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
            response.append(get_node_json(node, cloud))
        for relation in data['relations']:
            response.append(get_relation_json(relation))
    return response

# Relationship cytoscape.js 형태로 만들기
def get_relation_json(relation):
    data = {
        "source" : relation[2],
        "target" : relation[3],
        "weight" : 1,
        "group" : "coexp",
        "id" : "e"+str(relation[1]),
        "name": relation[4]
    }
    response = {
        "data" : data,
        "group" : "edges"
    }
    return response

# Defalut Rule 로그 디테일
def get_default_details(request):
    detected_rule = request['detected_rule']
    eventTime = request['eventTime']
    cloud = request['cloud']
    id = request['id']
    global graph
    cypher = f"""
    MATCH p=(rule:Rule:{cloud}{{ruleName:'{detected_rule}'}})<-[detected:DETECTED|FLOW_DETECTED]-(log:Log:{cloud} {{eventTime:'{eventTime}'}})
    WHERE ID(detected) = {id}
    WITH log
    MATCH p=(log)<-[:ACTED*..15]-(:Log)
    WITH NODES(COLLECT(p)[-1]) AS nodes, log
    UNWIND nodes as node
    RETURN
        ID(node) AS id,
        node.eventTime as eventTime,
        node.eventName as productName,
        split(node.eventSource, '.')[0] as actionType,
        node.eventType as resultType,
        node.sourceIPAddress as sourceIP,
        CASE
            WHEN ID(node) = ID(log) THEN 'detected'
            ELSE 'normal'
        END AS type
    ORDER BY eventTime DESC
    """
    results = graph.run(cypher).data()
    response = []
    for result in results:
        node = dict(result.items())
        node['cloud'] = cloud
        response.append(node)
    return response

# Flow Rule 로그 디테일
def get_flow_details(request):
    detected_rule = request['detected_rule']
    eventTime = request['eventTime']
    cloud = request['cloud']
    id = request['id']
    global graph
    cypher = f"""
    MATCH p=(rule:Rule:{cloud}{{ruleName:'{detected_rule}'}})<-[detected:DETECTED|FLOW_DETECTED]-(log:Log:{cloud} {{eventTime:'{eventTime}'}})
    WHERE ID(detected) = {id}
    WITH log, detected.path as path
    MATCH (log)<-[:FLOW*{{path:path}}]-(flow)
    WITH COLLECT(flow) as flows, log, path
    WITH flows + [log] as flows, path
    UNWIND flows as flow
    OPTIONAL MATCH (flow)<-[:FLOW{{path:path}}]-(flow2)
    WITH path, flow, flow2, flows,
        CASE
            WHEN flow.userIdentity_arn = flow2.userIdentity_arn THEN 'same'
            WHEN flow.userIdentity_arn <> flow2.userIdentity_arn THEN 'diff'
            WHEN flow.userIdentity_type = flow2.userIdentity_type THEN 'same'
            WHEN flow.userIdentity_type <> flow2.userIdentity_type THEN 'diff'
            WHEN flow2 IS NULL THEN 'diff'
            ELSE 'diff'
        END AS flow_check
    CALL apoc.do.when(
        flow_check = 'diff',
        "
            OPTIONAL MATCH (flow)<-[:ACTED*..10]-(view:Log)
            WITH COLLECT(view) as nodes, flow, path
            OPTIONAL MATCH (flow)-[:FLOW{{path:path}}]->(flow3)
            WITH nodes, flow,
                CASE
                    WHEN flow.userIdentity_arn = flow3.userIdentity_arn THEN 'same'
                    WHEN flow.userIdentity_arn <> flow3.userIdentity_arn THEN 'diff'
                    WHEN flow.userIdentity_type = flow3.userIdentity_type THEN 'same'
                    WHEN flow.userIdentity_type <> flow3.userIdentity_type THEN 'diff'
                    WHEN flow3 IS NULL THEN 'same'
                    ELSE 'same'
                END AS flow_check 
            CALL apoc.do.when(
                flow_check = 'same',
                \\\"
                    RETURN [] as nodes
                \\\",
                \\\"
                    OPTIONAL MATCH (flow)-[:ACTED*..5]->(view:Log)
                    RETURN COLLECT(view) as nodes
                \\\",
                {{flow:flow}}
            ) YIELD value
            WITH nodes + value.nodes as nodes
            RETURN nodes
        ",
        "
            MATCH p=(flow)<-[:ACTED*]-(flow2)
            WITH NODES(p) as nodes, path, flow, flow2
            UNWIND nodes as node
            WITH DISTINCT(node), path, flow, flow2
            WHERE ID(node) <> ID(flow) AND ID(node) <> ID(flow2)
            WITH COLLECT(node) as nodes, path, flow
            OPTIONAL MATCH (flow)-[:FLOW{{path:path}}]->(flow3)
            WITH nodes, flow, flow3, path,
                CASE
                    WHEN flow.userIdentity_arn = flow3.userIdentity_arn THEN 'same'
                    WHEN flow.userIdentity_arn <> flow3.userIdentity_arn THEN 'diff'
                    WHEN flow.userIdentity_type = flow3.userIdentity_type THEN 'same'
                    WHEN flow.userIdentity_type <> flow3.userIdentity_type THEN 'diff'
                    WHEN flow3 IS NULL THEN 'same'
                    ELSE 'same'
                END AS flow_check
            CALL apoc.do.when(
                flow_check = 'same',
                \\\"
                    RETURN [] AS nodes
                \\\",
                \\\"
                    OPTIONAL MATCH (flow)-[:ACTED*..5]->(view:Log)
                    RETURN COLLECT(view) as nodes
                \\\",
                {{flow:flow}}
            ) YIELD value
            WITH nodes + value.nodes as nodes
            return nodes
        ",
        {{flow:flow, path:path, flow2:flow2}}
    ) YIELD value
    UNWIND value.nodes as node
    WITH COLLECT(DISTINCT(node)) as nodes, flows
    UNWIND flows as flow
    WITH flows + nodes as nodes, COLLECT(ID(flow)) as ids
    UNWIND nodes as node
    RETURN
        ID(node) AS id,
        node.eventTime as eventTime,
        node.eventName as productName,
        split(node.eventSource, '.')[0] as actionType,
        node.eventType as resultType,
        node.sourceIPAddress as sourceIP,
        CASE 
            WHEN ID(node) IN ids THEN 'detected'
            ELSE 'normal'
        END AS type
    ORDER BY node.eventTime DESC
    """
    results = graph.run(cypher).data()
    response = []
    for result in results:
        node = dict(result.items())
        node['cloud'] = cloud
        response.append(node)
    return response