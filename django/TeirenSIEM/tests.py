# from django.shortcuts import render, redirect, HttpResponse
# from django.http import JsonResponse
# from pathlib import Path
# from pymongo import MongoClient
# from django.conf import settings
# from py2neo import Graph
# from datetime import datetime
# from django.utils import timezone
# import TeirenSIEM.v1 as aws
# import webAPP.django.TeirenSIEM.v1.graphdb as graphdb
# import json
# from TeirenSIEM.v1.alert import get_node_json, get_relation_json
# from TeirenSIEM.models import GridLayout
# from django.template.loader import render_to_string

# # LOCAL
# # graph = Graph("bolt://127.0.0.1:7687", auth=('neo4j', 'teiren001'))

# # NCP
# # host = settings.NEO4J_HOST
# # port = settings.NEO4J_PORT
# # password = settings.NEO4J_PASSWORD
# # username = settings.NEO4J_USERNAME

# # AWS
# host = settings.NEO4J['HOST']
# port = settings.NEO4J["PORT"]
# username = settings.NEO4J['USERNAME']
# password = settings.NEO4J['PASSWORD']
# graph = Graph(f"bolt://{host}:{port}", auth=(username, password))

# BASE_DIR = Path(__file__).resolve().parent.parent
# STATIC_DIR = BASE_DIR / 'staticfiles'

# # Create your tests here.


# def test(request):
#     # epoch = 1676374614161
#     # data = datetime.fromtimestamp(epoch/1000 + 9*3600, timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
#     # context = {'object': data}
#     # global graph
#     # cypher = f"""
#     # MATCH (a:Account {{name:'f-hk'}})
#     # CALL apoc.path.expandConfig(a, {{
#     #     relationshipFilter: "DETECTED|ACTED|DATE",
#     #     labelFilter: "/RULE",
#     #     minLevel: 1,
#     #     maxLevel: 10000}}) YIELD path
#     # UNWIND NODES(path) as nodes
#     # RETURN DISTINCT(nodes)
#     # """
#     # results = graph.run(cypher)
#     # results = graph.run(cypher)
#     # response = []
#     # for result in results:
#     #     nodes = dict(result.items())
#     #     for node in nodes.values():
#     #         response.append(get_node_json(node, 'AWS'))

        

#     # cypher2 = f"""
#     # MATCH p=(r:RULE:AWS {{ruleName:'delete_role_by_iam'}})<-[d:DETECTED]-(l:LOG:AWS {{eventTime:"2023-07-25T04:30:42Z"}})-[:ACTED|DATE*]-(a:Account)
#     # where id(d) = 270874
#     # UNWIND RELATIONSHIPS(p) as rel
#     # WITH DISTINCT(rel) as rel
#     # WITH
#     #     [
#     #         PROPERTIES(rel),
#     #         ID(rel),
#     #         ID(STARTNODE(rel)),
#     #         ID(ENDNODE(rel)),
#     #         TYPE(rel)
#     #     ] as relation
#     # RETURN COLLECT(relation) as relations
#     # """
#     # results = graph.run(cypher2)
#     # response2 = []
#     # for result in results:
#     #     data = dict(result)
#     #     for relation in data['relations']:
#     #         response2.append(get_relation_json(relation))
#     test = detected_rule = 'cli_update_user_with_accessToken'
#     eventTime = '2023-09-11T06:57:44Z'
#     cloud = 'Aws'
#     id = 3709
#     test = f"""
#     MATCH (rule:Rule:{cloud}{{ruleName:'{detected_rule}'}})<-[detected:FLOW_DETECTED]-(log:Log:{cloud}{{eventTime:'{eventTime}'}})-[check_rel:CHECK]->(check:Flow)
#     WHERE ID(detected) = {id} AND check_rel.path = detected.path
#     WITH log, detected, rule, check_rel, check
#     MATCH p=(log)<-[flow_rel:FLOW* {{path: detected.path}}]-(flow)-[check_rels:CHECK]->(checks:Flow)
#     WITH COLLECT(flow_rel[-1]) as flow_rel, COLLECT(flow) as flows, log, rule, detected,check, check_rel,detected.path as path,
#         COLLECT(checks) AS checks,
#         COLLECT(check_rels) AS check_rels
#     OPTIONAL MATCH (log)-[assumed:ASSUMED]->(role:Role)
#     WITH flows, path, log,
#         CASE
#             WHEN role IS NULL THEN [rule, check] + checks
#             ELSE [rule, check, role] + checks
#         END AS nodes,
#         CASE
#             WHEN assumed IS NULL THEN [detected, check_rel] + check_rels + flow_rel
#             ELSE [detected, check_rel, assumed] + check_rels + flow_rel
#         END AS relations
#     UNWIND flows as flow
#     OPTIONAL MATCH (flow)<-[:FLOW {{path:path}}]-(flow2)
#     WITH log, nodes, relations, path, flow, flow2,
#         CASE 
#             WHEN flow2 IS NULL THEN 'diff'
#             WHEN flow.userIdentity_arn <> flow2.userIdentity_arn THEN 'diff'
#             WHEN flow.userIdentity_type = flow2.userIdentity_type THEN 'same'
#             WHEN flow.userIdentity_type <> flow.userIdentity_type THEN 'diff'
#             ELSE 'same'
#         END AS flow_check
#     CALL apoc.do.when(
#         flow_check = 'diff',
#         "
#             MATCH (flow)-[:FLOW {{path:path}}]->(flow2)
#             WITH flow, flow2, path,
#                 CASE
#                     WHEN flow.userIdentity_arn IS NULL AND flow2.userIdentity_arn IS NULL THEN 'same'
#                     WHEN flow.userIdentity_arn = flow2.userIdentity_arn THEN 'same'
#                     WHEN flow.userIdentity_type = flow2.userIdentity_type THEN 'same'
#                     WHEN flow.userIdentity_type <> flow2.userIdentity_type THEN 'diff'
#                     ELSE 'diff'
#                 END AS flow_check
#             CALL apoc.do.when(
#                 flow_check = 'same',
#                 \\\"
#                     MATCH (flow)<-[:ACTED*]-(date:Date)<-[date_rel:DATE]-(account:Account)
#                     WITH flow, date, date_rel, account, flow2
#                     MATCH (flow)<-[:ACTED*]-(mid:Log)
#                     WITH flow, date, date_rel, account, mid.eventName as eventName, COUNT(mid) as cnt, flow2
#                     WITH flow, date, date_rel, account, SUM(cnt) as total, flow2,
#                         apoc.map.fromPairs(COLLECT([eventName,cnt])) as prop
#                     CALL apoc.create.vNode(['Analysis'], apoc.map.merge(prop,{{name:'Analysis',total:total}})) YIELD node AS analysis
#                     CALL apoc.create.vRelationship(date,'ANALYZE',{{}}, analysis) YIELD rel AS analyze1
#                     CALL apoc.create.vRelationship(analysis,'ANALYZE',{{}}, flow) YIELD rel AS analyze2
#                     WITH flow, flow2, [date, analysis, account] as nodes, [date_rel, analyze1, analyze2] as relations
#                     OPTIONAL MATCH (flow)-[assumed:ASSUMED]->(role:Role)
#                     WITH flow, flow2,
#                         CASE
#                             WHEN role IS NULL THEN nodes
#                             ELSE nodes + [role]
#                         END AS nodes,
#                         CASE
#                             WHEN assumed IS NULL THEN relations
#                             ELSE relations + [assumed]
#                         END AS relations
#                     OPTIONAL MATCH p=(flow)-[:ACTED|NEXT*]->(flow2)
#                     WITH flow, flow2, nodes, relations, NODES(p) as mid
#                     CALL apoc.do.when(
#                         SIZE(mid) <= 0,
#                         \\\\\\"
#                             MATCH (flow)-[acted:ACTED]->(flow2)
#                             RETURN [flow] as nodes, [acted] as relations
#                         \\\\\\",
#                         \\\\\\"
#                             MATCH p=(flow)-[:ACTED|NEXT*]->(flow2)
#                             WITH flow, flow2, NODES(p) as mids
#                             UNWIND mids as mid
#                             WITH flow, flow2, mid
#                             WHERE ID(mid)<>ID(flow) AND ID(mid) <> ID(flow2)
#                             WITH flow, flow2, mid.eventName as eventName, COUNT(mid) as cnt
#                             WITH flow, flow2, SUM(cnt) as total,
#                                 apoc.map.fromPairs(COLLECT([eventName,cnt])) as prop
#                             CALL apoc.create.vNode(['Analysis'], apoc.map.merge(prop,{{name:'Analysis', total: total}})) YIELD node AS analysis
#                             CALL apoc.create.vRelationship(flow,'ANALYZE',{{}}, analysis) YIELD rel AS analyze1
#                             CALL apoc.create.vRelationship(analysis,'ANALYZE',{{}}, flow2) YIELD rel AS analyze2
#                             RETURN [flow, analysis] as nodes, [analyze1, analyze2] as relations
#                         \\\\\\",
#                         {{flow:flow, flow2:flow2}}
#                     ) YIELD value
#                     WITH value.nodes + nodes as nodes, value.relations + relations as relations
#                     RETURN nodes, relations
#                 \\\",
#                 \\\"
#                     MATCH (flow)<-[:ACTED*]-(date:Date)<-[date_rel:DATE]-(account:Account)
#                     WITH flow, date, date_rel, account
#                     OPTIONAL MATCH (flow)<-[:ACTED*]-(mid:Log)
#                     WITH flow, date, date_rel, account, COLLECT(mid) as mid
#                     CALL apoc.do.when(
#                         SIZE(mid) = 0 ,
#                         \\\\\\"
#                             MATCH (flow)<-[acted:ACTED]-(date)
#                             RETURN [flow, date] as nodes, [acted] as relations
#                         \\\\\\",
#                         \\\\\\"
#                             MATCH (flow)<-[:ACTED*]-(mid:Log)
#                             WITH flow, date, mid.eventName as eventName, COUNT(mid) as cnt
#                             WITH flow, date, SUM(cnt) as total,
#                                 apoc.map.fromPairs(COLLECT([eventName,cnt])) as prop
#                             CALL apoc.create.vNode(['Analysis'], apoc.map.merge(prop,{{name:'Analysis', total: total}})) YIELD node AS analysis
#                             CALL apoc.create.vRelationship(date,'ANALYZE',{{}}, analysis) YIELD rel AS analyze1
#                             CALL apoc.create.vRelationship(analysis,'ANALYZE',{{}}, flow) YIELD rel AS analyze2
#                             RETURN [flow, date, analysis] as nodes, [analyze1, analyze2] as relations
#                         \\\\\\",
#                         {{flow: flow, date:date}}
#                     )YIELD value
#                     WITH value.nodes + [account] as nodes, value.relations + [date_rel] as relations, flow
#                     OPTIONAL MATCH (flow)-[view_rel:ACTED*..5]->(view:Log)
#                     WITH nodes, relations, COLLECT(view) as view, COLLECT(view_rel[-1]) as view_rel, flow
#                     WITH nodes + view as nodes, relations + view_rel as relations, flow
#                     OPTIONAL MATCH (flow)-[assumed:ASSUMED]->(role:Role)
#                     WITH
#                         CASE
#                             WHEN role IS NULL THEN nodes
#                             ELSE nodes + [role]
#                         END AS nodes,
#                         CASE
#                             WHEN assumed IS NULL THEN relations
#                             ELSE relations + [assumed]
#                         END AS relations
#                     RETURN nodes, relations
#                 \\\",
#                 {{flow:flow, flow2:flow2}}
#             ) YIELD value
#             RETURN value
#         ",
#         "
#             MATCH (flow)-[:FLOW{{path:path}}]->(flow2)
#             WITH flow, flow2,
#                 CASE
#                     WHEN flow.userIdentity_arn IS NULL AND flow2.userIdentity_arn IS NULL THEN 'same'
#                     WHEN flow.userIdentity_arn = flow2.userIdentity_arn THEN 'same'
#                     WHEN flow.userIdentity_type = flow2.userIdentity_type THEN 'same'
#                     WHEN flow.userIdentity_type <> flow2.userIdentity_type THEN 'diff'
#                     ELSE 'diff'
#                 END AS flow_check
#             CALL apoc.do.when(
#                 flow_check = 'same',
#                 \\\"
#                     MATCH p=(flow)-[ACTED|NEXT*]->(flow2)
#                     WITH flow, flow2, NODES(p) as mids
#                     UNWIND mids as mid
#                     WITH flow, flow2, mid
#                     WHERE ID(mid) <> ID(flow) AND ID(mid) <> ID(flow2)
#                     WITH mid.eventName as eventName, COUNT(mid) as cnt, flow, flow2
#                     WITH flow, flow2, SUM(cnt) as total, apoc.map.fromPairs(COLLECT([eventName,cnt])) as prop
#                     CALL apoc.create.vNode(['Analysis'], apoc.map.merge(prop,{{name:'Analysis', total:total}})) YIELD node AS analysis
#                     CALL apoc.create.vRelationship(flow,'ANALYZE',{{}}, analysis) YIELD rel AS analyze1
#                     CALL apoc.create.vRelationship(analysis,'ANALYZE',{{}}, flow2) YIELD rel AS analyze2
#                     WITH flow, analysis, [analyze1, analyze2] AS relations
#                     OPTIONAL MATCH (flow)-[assumed:ASSUMED]->(role:Role)
#                     WITH
#                         CASE
#                             WHEN role IS NULL THEN [flow, analysis]
#                             ELSE [flow, analysis, role]
#                         END AS nodes,
#                         CASE
#                             WHEN assumed IS NULL THEN relations
#                             ELSE relations + [assumed]
#                         END AS relations
#                     RETURN nodes, relations
#                 \\\",
#                 \\\"
#                     OPTIONAL MATCH (flow)-[view_rels:ACTED*..5]->(view:Log)
#                     WITH flow, COLLECT(view_rels[-1]) as view_rels, COLLECT(view) as view
#                     OPTIONAL MATCH (flow)-[assumed:ASSUMED]->(role:Role)
#                     WITH
#                         CASE
#                             WHEN role IS NULL THEN view + [flow]
#                             ELSE view + [flow, role]
#                         END AS nodes,
#                         CASE
#                             WHEN assumed IS NULL THEN view_rels
#                             ELSE view_rels + [assumed]
#                         END AS relations
#                     RETURN nodes, relations
#                 \\\",
#                 {{flow:flow, flow2:flow2}}
#             ) YIELD value
#             RETURN value
#         ",
#         {{flow:flow, path:path}}
#     ) YIELD value
#     UNWIND value.value.relations as relation
#     UNWIND value.value.nodes as node
#     WITH relations, nodes, log, path,
#         COLLECT(DISTINCT(node)) as nodes2,
#         COLLECT(DISTINCT(relation)) as relations2
#     WITH nodes + nodes2 as nodes, relations + relations2 as relations, log, path
#     MATCH (log)<-[:FLOW {{path:path}}]-(flow)
#     WITH log, nodes, relations,
#         CASE
#             WHEN log.userIdentity_arn <> flow.userIdentity_arn THEN 'diff'
#             WHEN log.userIdentity_arn = flow.userIdentity_arn THEN 'same'
#             WHEN log.userIdentity_type = flow.userIdentity_type THEN 'same'
#             WHEN log.userIdentity_type <> flow.userIdentity_type THEN 'diff'
#             ELSE 'diff'
#         END AS flow_check
#     CALL apoc.do.when(
#         flow_check = 'diff',
#         "
#             MATCH (log)<-[:ACTED*]-(date:Date)<-[date_rel:DATE]-(account:Account)
#             WITH log, date, account, date_rel
#             OPTIONAL MATCH (log)<-[:ACTED*]-(mid:Log)
#             WITH log, date, account, date_rel, COLLECT(mid) as mid
#             CALL.apoc.do.when(
#                 SIZE(mid) = 0,
#                 \\\"
#                     MATCH (log)<-[acted:acted]-(date)
#                     RETURN [log, date, account] as nodes, [acted, date_rel] as relations
#                 \\\",
#                 \\\"
#                     MATCH (log)<-[:ACTED*]-(mid:Log)
#                     WITH log, date, account, date_rel, mid.eventName as eventName, COUNT(mid) as cnt
#                     WITH log, date, account, date_rel, SUM(cnt) as total,
#                         apoc.map.fromPairs(COLLECT([eventName,cnt])) as prop
#                     CALL apoc.create.vNode(['Analysis'], apoc.map.merge(prop,{{name:'Analysis', total: total}})) YIELD node AS analysis
#                     CALL apoc.create.vRelationship(date,'ANALYZE',{{}}, analysis) YIELD rel AS analyze1
#                     CALL apoc.create.vRelationship(analysis,'ANALYZE',{{}}, log) YIELD rel AS analyze2
#                     RETURN [log, date, account, analysis] as nodes, [analyze1, analyze2, date_rel] as relations
#                 \\\",
#                 {{log:log, date:date, date_rel:date_rel, account:account}}
#             ) YIELD value
#             RETURN value
#         ",
#         "   
#             WITH {{nodes: [log], relations:[]}} as value
#             RETURN value
#         ",
#         {{log:log}}
#     ) YIELD value
#     WITH nodes + value.value.nodes as nodes, relations + value.value.relations as relations
#     UNWIND relations as relation
#     WITH nodes,
#         COLLECT([
#             PROPERTIES(relation),
#             ID(relation),
#             ID(STARTNODE(relation)),
#             ID(ENDNODE(relation)),
#             TYPE(relation)
#         ]) AS relations
#     RETURN nodes, relations
#     """
#     context = {'test': test}
#     return render(request, 'wish/test.html', context)


# def cyto(request):
#     global graph
#     cypher = '''
#     MATCH (l:LOG)-[re:DETECTED|FLOW_DETECTED]->(r:RULE{is_allow:1})
#     RETURN
#         id(l) as id,
#         head([label IN labels(l) WHERE label <> 'LOG']) AS cloud,
#         apoc.date.format(re.detected_time,'ms', 'yyyy-MM-dd HH:mm:ss', 'Asia/Seoul') AS detected_time,
#         r.comment as detectedAction,
#         l.actionDisplayName as actionDisplayName,
#         l.actionResultType as actionResultType,
#         l.eventTime as eventTime,
#         apoc.date.format(l.eventTime,'ms', 'yyyy-MM-dd HH:mm:ss', 'Asia/Seoul') AS eventTime_format,
#         l.sourceIp as sourceIp,
#         r.name as detected_rule
#     ORDER BY l.eventTime DESC
#     '''
#     results = graph.run(cypher)
#     data = []
#     filter = ['cloud', 'detected_rule', 'eventTime']
#     rule_number = {}
#     for result in results:
#         detail = dict(result.items())
#         form = {}
#         for key in filter:
#             if key != 'cloud':
#                 value = detail.pop(key)
#             else:
#                 value = detail[key]
#             form[key] = value
#             if key == 'detected_rule':
#                 if value in rule_number.keys():
#                     rule_number[value] += 1
#                 else:
#                     rule_number[value] = 1
#                 detail['rule_name'] = value+'#'+str(rule_number[value])
#                 form['rule_name'] = value+'#'+str(rule_number[value])
#         detail['form'] = form
#         data.append(detail)
#     context = {'data': data}
#     return render(request, 'wish/neo4j.html', context)


# def ajax_src(request):
#     if request.method == 'POST':
#         response = json.dumps({"w": '', "h": '', "content":"""
#         <div id="recentCollectedOverview" class="mb-1 pl-1 h-100">
#     <div class="card shadow h-100 w-100">
#         <!-- Card Header - Dropdown -->
#         <div class="card-header">
#             <div class="h6 m-0 font-weight-bold text-primary">최근 수집 로그 Overview</div>
#         </div>
#         <!-- Card Body -->
#         <div class="card-body pl-0 pb-0">
#             <div class="chart-area" style="height:100%;">
#                 <canvas id="recentOverview"></canvas>
#             </div>
#         </div>
#     </div>
# </div>
# <script src="/staticfiles/js/dashboard/recentOverview.js"></script>
# <script>
#     {"Month": ["2022/12", "2023/1", "2023/2", "2023/3", "2023/4", "2023/5", "2023/6", "2023/7", "2023/8", "2023/9"], "collected_month": [0, 0, 0, 0, 0, 11179, 116862, 3952, 137, 0]}
# </script>
# """})
#         return HttpResponse(response)


# def ajax_dst(request):
#     if request.method == 'POST':
#         layouts = GridLayout.objects.filter(name=request.POST['name'])
#         for layout in layouts:
#             items = json.loads(layout.data)
#         for item in items:
#             item['content'] = render_to_string(f"dashboard/items/{item['id']}.html")
#         response = json.dumps(items)
#         return HttpResponse(response)


# def ajax_js(request):
#     if request.method == 'POST':
#         data = request.POST.get('test')
#     else:
#         data = 'js fail'
#     return HttpResponse(data)


# def backup(request):
#     context = aws.log.backup()
#     return render(request, 'wish/test.html', context)
