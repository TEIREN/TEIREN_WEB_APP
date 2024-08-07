# # local
# import json
# import operator
# import traceback
# from common.neo4j.handler import Neo4jHandler
# # django
# from django.conf import settings
# from django.shortcuts import render, HttpResponse
# # 3rd party

# # AWS
# host = settings.NEO4J['HOST']
# port = settings.NEO4J["PORT"]
# username = settings.NEO4J['USERNAME']
# password = settings.NEO4J['PASSWORD']


# class Detection(Neo4jHandler):
#     def __init__(self, request) -> None:
#         super().__init__()
#         self.request = dict(request.POST.items()) if request.method == 'POST' else dict(
#             request.GET.items())
#         self.user_db = request.session.get('db_name')

#     def neo4j_graph(self):
#         try:
#             data = self.get_data()
#             details = self.get_log_details()
#             context = {'graph': json.dumps(data), 'details': details}
#             return context
#         except Exception as e:
#             print(traceback.print_exc())
#             return HttpResponse({'message': '다시 시도'})

#     def get_data(self):
#         # print(self.request)
#         rule_class = self.request['rule_class']
#         if rule_class == 'static':
#             data = self.get_static()
#         else:
#             data = self.get_dynamic()
#         return data

#     def get_log_details(self):
#         rule_class = self.request['rule_class']
#         if rule_class == 'static':
#             details = self.get_static_details()
#         else:
#             details = self.get_dynamic_details()
#         return details

#     # Node cytoscape.js 형태로 만들기
#     def get_node_json(self, node: dict, cloud):
#         data = {
#             "id": node.id,
#             "name": "",
#             "score": 400,
#             "query": True,
#             "gene": True
#         }
#         property_ = dict(node.items())
#         property_ = {key: property_[key] for key in sorted(property_.keys())}
#         if 'Log' in node.labels:
#             data['label'] = 'Log'
#             for key, value in property_.items():
#                 if key == 'eventName':
#                     data['name'] = value
#                 else:
#                     if any(x in key for x in ['responseElements', 'requestParameters', 'tls']):
#                         continue
#                     if 'userAgent' in key:
#                         continue
#                     if 'errorMessage' in key:
#                         value = value.replace('\'', '[', 1)
#                         value = value.replace('\'', ']', 1)
#                     if '\'' in str(value):
#                         value = value.replace('\'', '[', 1)
#                         value = value.replace('\'', ']', 1)
#                     data[key] = value
#         else:
#             if 'Flow' in node.labels:
#                 data['label'] = 'Flow'
#                 data['name'] = property_['flowName']
#             if 'Date' in node.labels:
#                 data['label'] = 'Date'
#             if 'Account' in node.labels:
#                 data['label'] = 'Account'
#                 data['score'] = 700
#             if 'Between' in node.labels:
#                 data['label'] = 'Between'
#                 property_ = dict(
#                     sorted(property_.items(), key=operator.itemgetter(1), reverse=True))
#             if 'Role' in node.labels:
#                 data['label'] = 'Role'
#             if 'Rule' in node.labels:
#                 data['label'] = 'Rule'
#                 data['name'] = property_['ruleName']
#             for key, value in property_.items():
#                 if key == 'name':
#                     value = str(value)
#                     value = value.split('_')[0]
#                 if any(x in key for x in ['responseElements', 'requestParameters', 'tls', 'query', 'ruleOperators', 'ruleValues', 'ruleKeys']):
#                     continue
#                 if 'errorMessage' in key:
#                     value = value.replace('\'', '[', 1)
#                     value = value.replace('\'', ']', 1)
#                 if key == 'date' or key == 'userName':
#                     value = str(value)
#                     data['name'] = value
#                 data[key] = value
#         response = {
#             "data": data,
#             "group": "nodes"
#         }
#         return response

#     # Default Rule
#     def get_static(self):
#         detected_rule = self.request['detected_rule']
#         eventTime = self.request['eventTime']
#         logType = self.request['resource']
#         id_ = self.request['id']

#         cypher = f"""
#         MATCH (rule:Rule:{logType}{{ruleName: '{detected_rule}'}})<-[detect:DETECTED]-(log:Log:{logType}{{eventTime:'{eventTime}'}})
#         WHERE ID(detect) = {id_}
#         WITH rule, detect, log
#         OPTIONAL MATCH p=(log)<-[:ACTED|NEXT*6]-(:Log)
#         CALL apoc.do.when(
#             p IS NULL,
#             "
#                 MATCH p=(log)<-[:ACTED|DATE*]-(:Account)
#                 WITH COLLECT(p)[-1] as p
#                 WITH NODES(p) as nodes, RELATIONSHIPS(p) as relations
#                 RETURN nodes, relations
#                 ",
#             "
#                 MATCH p=(log)<-[:ACTED|NEXT*..5]-(view:Log)
#                 WITH COLLECT(p)[-1] as p
#                 WITH NODES(p) as nodes, RELATIONSHIPS(p) as relations
#                 WITH nodes, relations, nodes[-1] as last
#                 MATCH (last)<-[:ACTED*]-(date:Date)<-[date_rel:DATE]-(account:Account)
#                 WITH nodes + [account] as nodes, relations + [date_rel] as relations, date, last
#                 MATCH (last)<-[:ACTED*]-(mid:Log)
#                 WITH mid.eventName as eventName, COUNT(mid) as cnt, last, date, nodes, relations
#                 WITH apoc.map.fromPairs(COLLECT([eventName, cnt])) as prop, nodes, relations, date, last, SUM(cnt) as total
#                 CALL apoc.create.vNode(['Between'], apoc.map.merge(prop,{{name: total}})) YIELD node AS analysis
#                 CALL apoc.create.vRelationship(date,'BETWEEN',{{}}, analysis) YIELD rel AS analyze1
#                 CALL apoc.create.vRelationship(analysis,'BETWEEN',{{}}, last) YIELD rel AS analyze2
#                 WITH nodes + [date,analysis] as nodes, relations + [analyze1,analyze2] as relations
#                 RETURN nodes, relations
#             ",
#             {{log:log}}
#         ) YIELD value
#         WITH value.nodes + [rule] as nodes, value.relations + [detect] as relations, log
#         OPTIONAL MATCH (log)-[assumed:ASSUMED]->(role:Role)
#         WITH
#             CASE
#                 WHEN role IS NULL THEN nodes
#                 ELSE nodes + [role]
#             END AS nodes,
#             CASE
#                 WHEN assumed IS NULL THEN relations
#                 ELSE relations + [assumed]
#             END AS relations
#         UNWIND relations as relation
#         WITH nodes,
#             COLLECT({{
#                 relation_id: ID(relation),
#                 start_node_id: ID(apoc.rel.startNode(relation)),
#                 end_node_id: ID(apoc.rel.endNode(relation)),
#                 relation_type: TYPE(relation)
#             }}) AS relations
#         RETURN nodes AS nodes, relations As relations
#         """
#         try:
#             # print(cypher)
#             results = self.run_data(database=self.user_db, query=cypher)
#         except Exception:
#             print(traceback.print_exc())

#         # type(results) = list
#         # results[0] = dict

#         # response = list
#         # response.append(<dict>)
#         # response = list
#         response = []
#         for node in results[0]['nodes']:
#             response.append(self.get_node_json(node, logType))
#         for relation in results[0]['relations']:
#             response.append(self.get_relation_json(relation))
#         return response

#     # Flow Rule
#     def get_dynamic(self):
#         detected_rule = self.request['detected_rule']
#         eventTime = self.request['eventTime']
#         logType = self.request['resource']
#         id_ = self.request['id']
#         cypher = f"""
#         MATCH (rule:Rule:{logType}{{ruleName:'{detected_rule}'}})<-[detected:FLOW_DETECTED]-(log:Log:{logType}{{eventTime:'{eventTime}'}})-[check_rel:CHECK]->(check:Flow)
#         WHERE ID(detected) = {id_} AND check_rel.path = detected.path
#         WITH log, detected, rule, check_rel, check
#         MATCH p=(log)<-[flow_rel:FLOW* {{path: detected.path}}]-(flow)-[check_rels:CHECK{{path:detected.path}}]->(checks:Flow)
#         WITH COLLECT(flow_rel[-1]) as flow_rel, COLLECT(flow) as flows, log, rule, detected,check, check_rel,detected.path as path,
#             COLLECT(checks) AS checks,
#             COLLECT(check_rels) AS check_rels
#         OPTIONAL MATCH (log)-[assumed:ASSUMED]->(role:Role)
#         WITH flows, path, log,
#             CASE
#                 WHEN role IS NULL THEN [rule, check] + checks
#                 ELSE [rule, check, role] + checks
#             END AS nodes,
#             CASE
#                 WHEN assumed IS NULL THEN [detected, check_rel] + check_rels + flow_rel
#                 ELSE [detected, check_rel, assumed] + check_rels + flow_rel
#             END AS relations
#         UNWIND flows as flow
#         OPTIONAL MATCH (flow)<-[:FLOW {{path:path}}]-(flow2)
#         WITH log, nodes, relations, path, flow, flow2,
#             CASE 
#                 WHEN flow2 IS NULL THEN 'diff'
#                 WHEN flow.userName = flow2.userName THEN 'same'
#                 WHEN flow.userName <> flow2.userName THEN 'diff'
#                 WHEN flow.userIdentity_arn <> flow2.userIdentity_arn THEN 'diff'
#                 WHEN flow.userIdentity_type = flow2.userIdentity_type THEN 'same'
#                 WHEN flow.userIdentity_type <> flow.userIdentity_type THEN 'diff'
#                 ELSE 'same'
#             END AS flow_check
#         CALL apoc.do.when(
#             flow_check = 'diff',
#             "
#                 MATCH (flow)-[:FLOW {{path:path}}]->(flow2)
#                 WITH flow, flow2, path,
#                     CASE
#                         WHEN flow.userName = flow2.userName THEN 'same'
#                         WHEN flow.userName <> flow2.userName THEN 'diff'
#                         WHEN flow.userIdentity_arn <> flow2.userIdentity_arn THEN 'diff'
#                         WHEN flow.userIdentity_arn = flow2.userIdentity_arn THEN 'same'
#                         WHEN flow.userIdentity_type = flow2.userIdentity_type THEN 'same'
#                         WHEN flow.userIdentity_type <> flow2.userIdentity_type THEN 'diff'
#                         ELSE 'diff'
#                     END AS flow_check
#                  CALL apoc.do.when(
#                     flow_check = 'same',
#                     \\\"
#                         MATCH (flow)<-[:ACTED*]-(date:Date)<-[date_rel:DATE]-(account:Account)
#                         WITH flow, date, date_rel, account, flow2
#                         OPTIONAL MATCH (flow)<-[:ACTED*]-(mid:Log)
#                         WITH flow, flow2, date, date_rel, account, COLLECT(mid) as mids
#                         CALL apoc.do.when(
#                             SIZE(mids) > 0,
#                             \\\\\\"
#                                 UNWIND mids as mid
#                                 WITH flow, date, date_rel, account, mid.eventName as eventName, COUNT(mid) as cnt
#                                 WITH flow, date, date_rel, account, SUM(cnt) as total,
#                                     apoc.map.fromPairs(COLLECT([eventName,cnt])) as prop
#                                 CALL apoc.create.vNode(['Between'], apoc.map.merge(prop,{{name:total}})) YIELD node AS analysis
#                                 CALL apoc.create.vRelationship(date,'BETWEEN',{{}}, analysis) YIELD rel AS analyze1
#                                 CALL apoc.create.vRelationship(analysis,'BETWEEN',{{}}, flow) YIELD rel AS analyze2
#                                 RETURN [date, analysis, account] as nodes, [date_rel, analyze1, analyze2] as relations
#                             \\\\\\",
#                             \\\\\\"
#                                 MATCH (flow)<-[acted_rel:ACTED]-(date)
#                                 RETURN [date, account] as nodes, [date_rel, acted_rel] as relations
#                             \\\\\\",
#                             {{flow:flow, date:date, date_rel:date_rel, account:account, mids:mids}}
#                         ) YIELD value
#                         WITH flow, flow2, value.nodes as nodes, value.relations as relations
#                         OPTIONAL MATCH (flow)-[assumed:ASSUMED]->(role:Role)
#                         WITH flow, flow2,
#                             CASE
#                                 WHEN role IS NULL THEN nodes
#                                 ELSE nodes + [role]
#                             END AS nodes,
#                             CASE
#                                 WHEN assumed IS NULL THEN relations
#                                 ELSE relations + [assumed]
#                             END AS relations
#                         OPTIONAL MATCH p=(flow)-[:ACTED|NEXT*]->(flow2)
#                         WITH flow, flow2, nodes, relations,
#                             CASE
#                                 WHEN NODES(p) IS NULL THEN []
#                                 ELSE NODES(p)
#                             END AS mid
#                         CALL apoc.do.when(
#                             SIZE(mid) <= 5,
#                             \\\\\\"
#                                 OPTIONAL MATCH p=(flow)-[acted:ACTED|NEXT*]->(flow2)
#                                 RETURN 
#                                     CASE
#                                         WHEN NODES(p) IS NULL THEN [flow]
#                                         ELSE NODES(p)
#                                     END AS nodes,
#                                     CASE
#                                         WHEN acted IS NULL THEN []
#                                         ELSE acted
#                                     END AS relations
#                             \\\\\\",
#                             \\\\\\"
#                                 MATCH p=(flow)-[:ACTED|NEXT*]->(flow2)
#                                 WITH flow, flow2, NODES(p) as mids
#                                 UNWIND mids as mid
#                                 WITH flow, flow2, mid
#                                 WHERE ID(mid)<>ID(flow) AND ID(mid) <> ID(flow2)
#                                 WITH flow, flow2, mid.eventName as eventName, COUNT(mid) as cnt
#                                 WITH flow, flow2, SUM(cnt) as total,
#                                     apoc.map.fromPairs(COLLECT([eventName,cnt])) as prop
#                                 CALL apoc.create.vNode(['Between'], apoc.map.merge(prop,{{name: total}})) YIELD node AS analysis
#                                 CALL apoc.create.vRelationship(flow,'BETWEEN',{{}}, analysis) YIELD rel AS analyze1
#                                 CALL apoc.create.vRelationship(analysis,'BETWEEN',{{}}, flow2) YIELD rel AS analyze2
#                                 RETURN [flow, analysis] as nodes, [analyze1, analyze2] as relations
#                             \\\\\\",
#                             {{flow:flow, flow2:flow2}}
#                         ) YIELD value
#                         WITH value.nodes + nodes as nodes, value.relations + relations as relations
#                         RETURN nodes, relations
#                     \\\",
#                     \\\"
#                         MATCH (flow)<-[:ACTED*]-(date:Date)<-[date_rel:DATE]-(account:Account)
#                         WITH flow, date, date_rel, account
#                         OPTIONAL MATCH (flow)<-[:ACTED*]-(mid:Log)
#                         WITH flow, date, date_rel, account, COLLECT(mid) as mid
#                         CALL apoc.do.when(
#                             SIZE(mid) = 0 ,
#                             \\\\\\"
#                                 MATCH (flow)<-[acted:ACTED]-(date)
#                                 RETURN [flow, date] as nodes, [acted] as relations
#                             \\\\\\",
#                             \\\\\\"
#                                 MATCH (flow)<-[:ACTED*]-(mid:Log)
#                                 WITH flow, date, mid.eventName as eventName, COUNT(mid) as cnt
#                                 WITH flow, date, SUM(cnt) as total,
#                                     apoc.map.fromPairs(COLLECT([eventName,cnt])) as prop
#                                 CALL apoc.create.vNode(['Between'], apoc.map.merge(prop,{{name: total}})) YIELD node AS analysis
#                                 CALL apoc.create.vRelationship(date,'BETWEEN',{{}}, analysis) YIELD rel AS analyze1
#                                 CALL apoc.create.vRelationship(analysis,'BETWEEN',{{}}, flow) YIELD rel AS analyze2
#                                 RETURN [flow, date, analysis] as nodes, [analyze1, analyze2] as relations
#                             \\\\\\",
#                             {{flow: flow, date:date}}
#                         )YIELD value
#                         WITH value.nodes + [account] as nodes, value.relations + [date_rel] as relations, flow
#                         OPTIONAL MATCH (flow)-[view_rel:ACTED*..5]->(view:Log)
#                         WITH nodes, relations, COLLECT(view) as view, COLLECT(view_rel[-1]) as view_rel, flow
#                         WITH nodes + view as nodes, relations + view_rel as relations, flow
#                         OPTIONAL MATCH (flow)-[assumed:ASSUMED]->(role:Role)
#                         WITH
#                             CASE
#                                 WHEN role IS NULL THEN nodes
#                                 ELSE nodes + [role]
#                             END AS nodes,
#                             CASE
#                                 WHEN assumed IS NULL THEN relations
#                                 ELSE relations + [assumed]
#                             END AS relations
#                         RETURN nodes, relations
#                     \\\",
#                     {{flow:flow, flow2:flow2}}
#                 ) YIELD value
#                 RETURN value
#             ",
#             "
#                 MATCH (flow)-[:FLOW{{path:path}}]->(flow2)
#                 WITH flow, flow2,
#                     CASE
#                         WHEN flow.userIdentity_arn IS NULL AND flow2.userIdentity_arn IS NULL THEN 'same'
#                         WHEN flow.userName = flow2.userName THEN 'same'
#                         WHEN flow.userName <> flow2.userName THEN 'diff'
#                         WHEN flow.userIdentity_arn = flow2.userIdentity_arn THEN 'same'
#                         WHEN flow.userIdentity_type = flow2.userIdentity_type THEN 'same'
#                         WHEN flow.userIdentity_type <> flow2.userIdentity_type THEN 'diff'
#                         ELSE 'diff'
#                     END AS flow_check
#                 CALL apoc.do.when(
#                     flow_check = 'same',
#                     \\\"
#                         MATCH p=(flow)-[:ACTED|NEXT*]->(flow2)
#                         WITH flow, flow2, NODES(p) as mids
#                         UNWIND mids as mid
#                         WITH flow, flow2, mid
#                         WHERE ID(mid) <> ID(flow) AND ID(mid) <> ID(flow2)
#                         WITH mid.eventName as eventName, COUNT(mid) as cnt, flow, flow2
#                         WITH flow, flow2, SUM(cnt) as total, apoc.map.fromPairs(COLLECT([eventName,cnt])) as prop
#                         CALL apoc.create.vNode(['Between'], apoc.map.merge(prop,{{name:total}})) YIELD node AS analysis
#                         CALL apoc.create.vRelationship(flow,'BETWEEN',{{}}, analysis) YIELD rel AS analyze1
#                         CALL apoc.create.vRelationship(analysis,'BETWEEN',{{}}, flow2) YIELD rel AS analyze2
#                         WITH flow, analysis, [analyze1, analyze2] AS relations
#                         OPTIONAL MATCH (flow)-[assumed:ASSUMED]->(role:Role)
#                         WITH
#                             CASE
#                                 WHEN role IS NULL THEN [flow, analysis]
#                                 ELSE [flow, analysis, role]
#                             END AS nodes,
#                             CASE
#                                 WHEN assumed IS NULL THEN relations
#                                 ELSE relations + [assumed]
#                             END AS relations
#                         RETURN nodes, relations
#                     \\\",
#                     \\\"
#                         OPTIONAL MATCH (flow)-[view_rels:ACTED*..5]->(view:Log)
#                         WITH flow, COLLECT(view_rels[-1]) as view_rels, COLLECT(view) as view
#                         OPTIONAL MATCH (flow)-[assumed:ASSUMED]->(role:Role)
#                         WITH
#                             CASE
#                                 WHEN role IS NULL THEN view + [flow]
#                                 ELSE view + [flow, role]
#                             END AS nodes,
#                             CASE
#                                 WHEN assumed IS NULL THEN view_rels
#                                 ELSE view_rels + [assumed]
#                             END AS relations
#                         RETURN nodes, relations
#                     \\\",
#                     {{flow:flow, flow2:flow2}}
#                 ) YIELD value
#                 RETURN value
#             ",
#             {{flow:flow, path:path}}
#         ) YIELD value
#         WITH nodes, relations, log, path,value.value.nodes AS val_nodes, value.value.relations AS val_relations
#         CALL apoc.do.case([
#             val_nodes IS NULL,
#             "
#                 RETURN [] AS val_nodes, [] as val_relations
#             ",
#             val_nodes IS NOT NULL,
#             "
#                 UNWIND val_nodes as val_node
#                 UNWIND val_relations as val_relation
#                 RETURN COLLECT(DISTINCT(val_node)) AS val_nodes, COLLECT(DISTINCT(val_relation)) AS val_relations
#             "
#         ],
#             "
#                 UNWIND val_nodes as val_node
#                 UNWIND val_relations as val_relation
#                 RETURN COLLECT(DISTINCT(val_node)) AS val_nodes, COLLECT(DISTINCT(val_relation)) AS val_relations
#             ",
#         {{val_nodes:val_nodes, val_relations:val_relations}}) YIELD value
#         WITH nodes + value.val_nodes AS nodes, relations + value.val_relations AS relations, log, path
#         MATCH (log)<-[:FLOW {{path:path}}]-(flow)
#             WITH log, nodes, relations,
#                 CASE
#                     WHEN log.userName = flow.userName THEN 'same'
#                     WHEN log.userName <> flow.userName THEN 'diff'
#                     WHEN log.userIdentity_arn <> flow.userIdentity_arn THEN 'diff'
#                     WHEN log.userIdentity_arn = flow.userIdentity_arn THEN 'same'
#                     WHEN log.userIdentity_type = flow.userIdentity_type THEN 'same'
#                     WHEN log.userIdentity_type <> flow.userIdentity_type THEN 'diff'
#                     ELSE 'diff'
#                 END AS flow_check
#         CALL apoc.do.when(
#             flow_check = 'diff',
#             "
#                 MATCH (log)<-[:ACTED*]-(date:Date)<-[date_rel:DATE]-(account:Account)
#                 WITH log, date, account, date_rel
#                 OPTIONAL MATCH (log)<-[:ACTED*]-(mid:Log)
#                 WITH log, date, account, date_rel, COLLECT(mid) as mid
#                 CALL apoc.do.when(
#                     SIZE(mid) = 0,
#                     \\\"
#                         MATCH (log)<-[acted:acted]-(date)
#                         RETURN [log, date, account] as nodes, [acted, date_rel] as relations
#                     \\\",
#                     \\\"
#                         MATCH (log)<-[:ACTED*]-(mid:Log)
#                         WITH log, date, account, date_rel, mid.eventName as eventName, COUNT(mid) as cnt
#                         WITH log, date, account, date_rel, SUM(cnt) as total,
#                             apoc.map.fromPairs(COLLECT([eventName,cnt])) as prop
#                         CALL apoc.create.vNode(['Between'], apoc.map.merge(prop,{{name:total}})) YIELD node AS analysis
#                         CALL apoc.create.vRelationship(date,'BETWEEN',{{}}, analysis) YIELD rel AS analyze1
#                         CALL apoc.create.vRelationship(analysis,'BETWEEN',{{}}, log) YIELD rel AS analyze2
#                         RETURN [log, date, account, analysis] as nodes, [analyze1, analyze2, date_rel] as relations
#                     \\\",
#                     {{log:log, date:date, date_rel:date_rel, account:account}}
#                 ) YIELD value
#                 RETURN value
#             ",
#             "
#                 WITH {{nodes: [log], relations:[]}} as value
#                 RETURN value
#             ",
#             {{log:log}}
#         ) YIELD value
#         WITH nodes + value.value.nodes as nodes, relations + value.value.relations as relations
#         UNWIND relations as relation
#         WITH nodes,
#             COLLECT({{
#                 relation_id: ID(relation),
#                 start_node_id: ID(apoc.rel.startNode(relation)),
#                 end_node_id: ID(apoc.rel.endNode(relation)),
#                 relation_type: TYPE(relation)
#             }}) AS relations
#         RETURN nodes, relations
#         """
#         # print(cypher)
#         results = self.run_records(database=self.user_db, query=cypher)
#         response = []
#         for result in results:
#             for node in result['nodes']:
#                 response.append(self.get_node_json(node, logType))
#             for relation in result['relations']:
#                 response.append(self.get_relation_json(relation))
#         return response

#     # Defalut Rule 로그 디테일
#     def get_static_details(self):
#         detected_rule = self.request['detected_rule']
#         eventTime = self.request['eventTime']
#         logType = self.request['resource']
#         id_ = self.request['id']
#         cypher = f"""
#         MATCH p=(rule:Rule:{logType}{{ruleName:'{detected_rule}'}})<-[detected:DETECTED|FLOW_DETECTED]-(log:Log:{logType} {{eventTime:'{eventTime}'}})
#         WHERE ID(detected) = {id_}
#         WITH log
#         OPTIONAL MATCH p=(log)<-[:ACTED|NEXT*..15]-(:Log)
#         WITH NODES(COLLECT(p)[-1]) AS nodes, log
#         WITH log,
#         CASE
#             WHEN nodes IS NULL THEN [log]
#             ELSE nodes + [log]
#         END AS nodes
#         UNWIND nodes as node
#         WITH DISTINCT(node), log
#         RETURN
#             ID(node) AS id,
#             node.eventTime as eventTime,
#             node.eventName as eventName,
#             CASE
#                 WHEN node.eventSource IS NOT NULL THEN split(node.eventSource, '.')[0]
#                 ELSE '-'
#             END AS eventType,
#             CASE
#                 WHEN node.eventType IS NOT NULL THEN node.eventType
#                 WHEN node.eventResult IS NOT NULL THEN node.eventResult
#                 ELSE '-'
#             END AS eventResult,
#             CASE
#                 WHEN node.sourceIPAddress IS NOT NULL THEN node.sourceIPAddress
#                 WHEN node.sourceIp IS NOT NULL THEN node.sourceIp
#                 ELSE '-'
#             END AS sourceIP,
#             CASE
#                 WHEN ID(node) = ID(log) THEN 'detected'
#                 ELSE 'normal'
#             END AS type
#         ORDER BY eventTime DESC
#         """
#         print(cypher)
#         results = self.run_data(database=self.user_db, query=cypher)
#         response = []
#         for result in results:
#             # result: <Record>
#             node = dict(result.items())
#             node['logType'] = logType
#             if logType in ['Aws', 'Ncp', 'Nhn', 'Kt']:
#                 node['resourceType'] = 'cloud'
#             elif logType in ['Teiren', 'Officekeeper']:
#                 node['resourceType'] = 'solution'
#             else:
#                 node['resourceType'] = 'system'
#             response.append(node)
#         return response

#         # Flow Rule 로그 디테일
#     def get_dynamic_details(self):
#         detected_rule = self.request['detected_rule']
#         eventTime = self.request['eventTime']
#         logType = self.request['resource']
#         id_ = self.request['id']
#         cypher = f"""
#         MATCH p=(rule:Rule:{logType}{{ruleName:'{detected_rule}'}})<-[detected:DETECTED|FLOW_DETECTED]-(log:Log:{logType} {{eventTime:'{eventTime}'}})
#         WHERE ID(detected) = {id_}
#         WITH log, detected.path as path
#         MATCH (log)<-[:FLOW*{{path:path}}]-(flow)
#         WITH COLLECT(flow) as flows, log, path
#         WITH flows + [log] as flows, path
#         UNWIND flows as flow
#         OPTIONAL MATCH (flow)<-[:FLOW{{path:path}}]-(flow2)
#         WITH path, flow, flow2, flows,
#             CASE
#                 WHEN flow.userName = flow2.userName THEN 'same'
#                 WHEN flow.userName <> flow2.userName THEN 'diff'
#                 WHEN flow.userIdentity_arn = flow2.userIdentity_arn THEN 'same'
#                 WHEN flow.userIdentity_arn <> flow2.userIdentity_arn THEN 'diff'
#                 WHEN flow.userIdentity_type = flow2.userIdentity_type THEN 'same'
#                 WHEN flow.userIdentity_type <> flow2.userIdentity_type THEN 'diff'
#                 WHEN flow2 IS NULL THEN 'diff'
#                 ELSE 'diff'
#             END AS flow_check
#         CALL apoc.do.when(
#             flow_check = 'diff',
#             "
#                 OPTIONAL MATCH (flow)<-[:ACTED*..10]-(view:Log)
#                 WITH COLLECT(view) as nodes, flow, path
#                 OPTIONAL MATCH (flow)-[:FLOW{{path:path}}]->(flow3)
#                 WITH nodes, flow,
#                     CASE
#                         WHEN flow.userName = flow3.userName THEN 'same'
#                         WHEN flow.userName <> flow3.userName THEN 'diff'
#                         WHEN flow.userIdentity_arn = flow3.userIdentity_arn THEN 'same'
#                         WHEN flow.userIdentity_arn <> flow3.userIdentity_arn THEN 'diff'
#                         WHEN flow.userIdentity_type = flow3.userIdentity_type THEN 'same'
#                         WHEN flow.userIdentity_type <> flow3.userIdentity_type THEN 'diff'
#                         WHEN flow3 IS NULL THEN 'same'
#                         ELSE 'same'
#                     END AS flow_check 
#                 CALL apoc.do.when(
#                     flow_check = 'same',
#                     \\\"
#                         RETURN [] as nodes
#                     \\\",
#                     \\\"
#                         OPTIONAL MATCH (flow)-[:ACTED*..5]->(view:Log)
#                         RETURN COLLECT(view) as nodes
#                     \\\",
#                     {{flow:flow}}
#                 ) YIELD value
#                 WITH nodes + value.nodes as nodes
#                 RETURN nodes
#             ",
#             "
#                 MATCH p=(flow)<-[:ACTED*]-(flow2)
#                 WITH NODES(p) as nodes, path, flow, flow2
#                 UNWIND nodes as node
#                 WITH DISTINCT(node), path, flow, flow2
#                 WHERE ID(node) <> ID(flow) AND ID(node) <> ID(flow2)
#                 WITH COLLECT(node) as nodes, path, flow
#                 OPTIONAL MATCH (flow)-[:FLOW{{path:path}}]->(flow3)
#                 WITH nodes, flow, flow3, path,
#                     CASE
#                         WHEN flow.userName = flow3.userName THEN 'same'
#                         WHEN flow.userName <> flow3.userName THEN 'diff'
#                         WHEN flow.userIdentity_arn = flow3.userIdentity_arn THEN 'same'
#                         WHEN flow.userIdentity_arn <> flow3.userIdentity_arn THEN 'diff'
#                         WHEN flow.userIdentity_type = flow3.userIdentity_type THEN 'same'
#                         WHEN flow.userIdentity_type <> flow3.userIdentity_type THEN 'diff'
#                         WHEN flow3 IS NULL THEN 'same'
#                         ELSE 'same'
#                     END AS flow_check
#                 CALL apoc.do.when(
#                     flow_check = 'same',
#                     \\\"
#                         RETURN [] AS nodes
#                     \\\",
#                     \\\"
#                         OPTIONAL MATCH (flow)-[:ACTED*..5]->(view:Log)
#                         RETURN COLLECT(view) as nodes
#                     \\\",
#                     {{flow:flow}}
#                 ) YIELD value
#                 WITH nodes + value.nodes as nodes
#                 return nodes
#             ",
#             {{flow:flow, path:path, flow2:flow2}}
#         ) YIELD value
#         WITH flows, value.nodes as nodes
#         CALL apoc.do.when(
#             SIZE(nodes) < 1,
#             "
#                 UNWIND flows as flow
#                 WITH flows as nodes, COLLECT(ID(flow)) as ids
#                 RETURN nodes, ids
#             ",
#             "
#                 UNWIND nodes as node
#                 WITH COLLECT(DISTINCT(node)) as nodes, flows
#                 UNWIND flows as flow
#                 WITH flows + nodes as nodes, COLLECT(ID(flow)) as ids
#                 RETURN nodes, ids
#             ",
#             {{flows:flows, nodes:nodes}}
#         ) YIELD value
#         WITH value.nodes as nodes, value.ids as ids
#         UNWIND nodes as node
#         WITH DISTINCT(node), ids
#         RETURN
#             ID(node) AS id,
#             node.eventTime as eventTime,
#             node.eventName as eventName,
#             CASE
#                 WHEN node.eventSource IS NOT NULL THEN split(node.eventSource, '.')[0]
#                 ELSE '-'
#             END AS eventType,
#             CASE
#                 WHEN node.eventType IS NOT NULL THEN node.eventType
#                 WHEN node.eventResult IS NOT NULL THEN node.eventResult
#                 ELSE '-'
#             END AS eventResult,
#             CASE
#                 WHEN node.sourceIPAddress IS NOT NULL THEN node.sourceIPAddress
#                 WHEN node.sourceIp IS NOT NULL THEN node.sourceIp
#                 ELSE '-'
#             END AS sourceIP,
#             CASE 
#                 WHEN ID(node) IN ids THEN 'detected'
#                 ELSE 'normal'
#             END AS type
#         ORDER BY node.eventTime DESC
#         """
#         print(cypher)
#         results = self.run_data(database=self.user_db, query=cypher)
#         response = []
#         for result in results:
#             node = dict(result.items())
#             node['logType'] = logType
#             if logType in ['Aws', 'Ncp', 'Nhn', 'Kt']:
#                 node['resourceType'] = 'cloud'
#             elif logType in ['Teiren', 'Officekeeper']:
#                 node['resourceType'] = 'solution'
#             else:
#                 node['resourceType'] = 'system'
#             response.append(node)
#         return response

#     # Relationship cytoscape.js 형태로 만들기
#     def get_relation_json(self, relation):
#         data = {
#             "source": relation['start_node_id'],
#             "target": relation['end_node_id'],
#             "weight": 1,
#             "group": "coexp",
#             "id": "e"+str(relation['relation_id']),
#             "name": relation['relation_type']
#         }
#         response = {
#             "data": data,
#             "group": "edges"
#         }
#         return response