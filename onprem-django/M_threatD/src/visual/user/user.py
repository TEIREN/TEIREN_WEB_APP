# # local
# import json, operator
# from M_threatD.src.notification.detection import Detection
# from common.neo4j.handler import Neo4jHandler

# # django
# from django.shortcuts import HttpResponse
# from django.conf import settings

# ## NCP
# # host = settings.NEO4J_HOST
# # port = settings.NEO4J_PORT
# # password = settings.NEO4J_PASSWORD
# # username = settings.NEO4J_USERNAME

# ## AWS
# host = settings.NEO4J['HOST']
# port = settings.NEO4J["PORT"]
# username = settings.NEO4J['USERNAME']
# password = settings.NEO4J['PASSWORD']

# class UserThreat(Neo4jHandler):
#     def __init__(self, request) -> None:
#         super().__init__()
#         self.request = dict(request.POST.items()) if request.method == 'POST' else dict(request.GET.items())
#         self.user_db = request.session.get('db_name')

#     # 사용자 중심 분석 그래프 시각화
#     def user_graph(self):
#         if isinstance(self.request, dict) :
#             data = self.get_user_static_data()
#             data += self.get_user_dynamic_data()
#             table = self.get_user_table()
#             context = {'graph': json.dumps(data), 'table': table }
#             return context
#         return HttpResponse('다시 시도')
    
#     def get_user_static_data(self):
#         account = self.request['account']
#         resource = self.request['resource']
#         cypher = f"""
#         MATCH (account:Account)-[:DATE|ACTED*]->(log:Log)-[detected:DETECTED]->(rule:Rule:{resource})
#         WHERE account.name = '{account}' or account.userName = '{account}'
#         WITH rule, account, detected, log
#         MATCH (log)<-[:ACTED*]-(date:Date)<-[date_rel:DATE]-(account)
#         WITH log,date,
#             [rule, account] as nodes, [detected, date_rel] as relations
#         OPTIONAL MATCH (log)<-[:ACTED*]-(mid:Log)
#         WITH nodes, relations, log, date, COLLECT(mid) as mid_c
#         CALL apoc.do.when(
#             SIZE(mid_c) < 1,
#             "
#                 MATCH (log)<-[acted:ACTED]-(date)
#                 RETURN [log, date] as nodes, [acted] as relations
#             ",
#             "
#                 WITH log, date, mid_c
#                 UNWIND mid_c as mid
#                 WITH log, date, mid.eventName as eventName, count(mid) as cnt
#                 WITH log, date, SUM(cnt) AS total, apoc.map.fromPairs(COLLECT([eventName, cnt])) as prop
#                 CALL apoc.create.vNode(['Between'], apoc.map.merge(prop,{{name:total}})) YIELD node AS analysis
#                 CALL apoc.create.vRelationship(date,'BETWEEN',{{}}, analysis) YIELD rel AS analyze1
#                 CALL apoc.create.vRelationship(analysis,'BETWEEN',{{}}, log) YIELD rel AS analyze2
#                 RETURN [log, date, analysis] as nodes, [analyze1, analyze2] as relations
#             ",
#             {{log:log, date:date, mid_c:mid_c}}
#         ) YIELD value
#         WITH nodes + value.nodes as nodes, relations + value.relations as relations, log
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
#         UNWIND nodes AS node
#         WITH COLLECT(DISTINCT(relation)) as relations, COLLECT(DISTINCT(node)) as nodes
#         UNWIND relations as relation
#         WITH nodes,
#         COLLECT({{
#             relation_id: ID(relation),
#             start_node_id: ID(apoc.rel.startNode(relation)),
#             end_node_id: ID(apoc.rel.endNode(relation)),
#             relation_type: TYPE(relation)
#         }}) AS relations
#         return nodes, relations
#         """
#         results = self.run_data(database=self.user_db, query=cypher)
#         response = []
#         for result in results:
#             for node in result['nodes']:
#                 response.append(self.get_node_json(node, resource))
#             for relation in result['relations']:
#                 response.append(self.get_relation_json(relation))
#         return response
    
#     def get_user_dynamic_data(self):
#         account = self.request['account']
#         resource = self.request['resource']
#         cypher = f"""
#         MATCH (account:Account)-[:DATE|ACTED*]->(log:Log)-[detected:FLOW_DETECTED]->(rule:Rule:{resource})
#         WHERE account.name = '{account}' OR account.userName = '{account}'
#         WITH [rule, account] AS nodes, detected, log, account
#         OPTIONAL MATCH (log)-[assumed:ASSUMED]->(role:Role)
#         WITH log, detected.path AS path, account,
#             CASE
#                 WHEN role IS NULL THEN nodes
#                 ELSE nodes + [role]
#             END AS nodes,
#             CASE
#                 WHEN assumed IS NULL THEN [detected]
#                 ELSE [detected, assumed]
#             END AS relations
#         OPTIONAL MATCH (check:Flow)<-[check_rel:CHECK {{path:path}}]-(log)
#         WITH log, path, nodes, relations, check, check_rel, account
#         OPTIONAL MATCH (log)<-[flow_rels:FLOW* {{path: path}}]-(flow)
#         WHERE flow.userIdentity_arn = log.userIdentity_arn OR log.userName = log.userName
#         WITH nodes, log, relations, flow, flow_rels[-1] AS flow_rel, check, check_rel, path, account
#         OPTIONAL MATCH (flow)-[check_rels:CHECK {{path: path}}]->(checks:Flow)
#         WITH nodes, relations, check, check_rel, flow_rel, account, log,
#             COLLECT(checks) AS checks,
#             COLLECT(check_rels) AS check_rels,
#             COLLECT(flow) AS flow
#         WITH nodes + checks + [check] as nodes, relations + check_rels + [check_rel, flow_rel] AS relations, flow, account, log
#         WITH nodes + flow AS nodes, relations AS relations, flow[-1] AS last, account, log
#         CALL apoc.do.when(
#             last IS NULL,
#             "
#                 MATCH (log)<-[:ACTED*]-(date:Date)<-[date_rel:DATE]-(account)
#                 RETURN [log, account] AS nodes, [date_rel] AS relations, log, date
#             ",
#             "
#                 MATCH (last)<-[:ACTED*]-(date:Date)<-[date_rel:DATE]-(account)
#                 RETURN [log, account] AS nodes, [date_rel] AS relations, last AS log, date
#             ",
#             {{log:log, last:last, account:account}}
#         ) YIELD value
#         WITH nodes + value.nodes AS nodes, relations + value.relations AS relations,
#             value.log AS log, value.date AS date
#         OPTIONAL MATCH (log)<-[:ACTED*]-(mid:Log)
#         WITH nodes, relations , log, date, COLLECT(mid) AS mid_c
#         CALL apoc.do.when(
#             SIZE(mid_c) < 1,
#             "
#                 MATCH (log)<-[acted:ACTED]-(date)
#                 RETURN [date] AS nodes, [acted] AS relations
#             ",
#             "
#                 WITH log, date, mid_c
#                 UNWIND mid_c AS mid
#                 WITH log, date, mid.eventName AS eventName, COUNT(mid) AS cnt
#                 WITH log, date, SUM(cnt) AS total, apoc.map.fromPairs(COLLECT([eventName, cnt])) AS prop
#                 CALL apoc.create.vNode(['Between'], apoc.map.merge(prop,{{name:total}})) YIELD node AS analysis
#                 CALL apoc.create.vRelationship(date,'BETWEEN',{{}}, analysis) YIELD rel AS analyze1
#                 CALL apoc.create.vRelationship(analysis,'BETWEEN',{{}}, log) YIELD rel AS analyze2
#                 RETURN [date, analysis] AS nodes, [analyze1, analyze2] as relations
#             ",
#             {{log:log, mid_c:mid_c, date:date}}
#         ) YIELD value
#         WITH nodes + value.nodes AS nodes, relations + value.relations AS relations
#         UNWIND nodes AS node
#         UNWIND relations AS relation
#         WITH COLLECT(DISTINCT(node)) AS nodes, COLLECT(DISTINCT(relation)) AS relations
#         UNWIND relations AS relation
#         WITH nodes,
#         COLLECT({{
#             relation_id: ID(relation),
#             start_node_id: ID(apoc.rel.startNode(relation)),
#             end_node_id: ID(apoc.rel.endNode(relation)),
#             relation_type: TYPE(relation)
#         }}) AS relations
#         RETURN nodes, relations
#         """
#         results = self.run_data(database=self.user_db, query=cypher)
#         response = []
#         for result in results:
#             for node in result['nodes']:
#                 response.append(self.get_node_json(node, resource))
#             for relation in result['relations']:
#                 response.append(self.get_relation_json(relation))
#         return response

#     def get_user_table(self):
#         account = self.request['account']
#         cypher = f"""
#         MATCH p=(r:Rule)<-[d:DETECTED|FLOW_DETECTED]-(l:Log)<-[:ACTED|DATE*]-(a:Account)
#         WHERE a.name = '{account}' or a.userName = '{account}'
#         RETURN
#             DISTINCT(ID(d)) AS id,
#             r.ruleName AS detected_rule,
#             l.eventTime AS eventTime,
#             apoc.date.format(apoc.date.parse(l.eventTime, "ms", "yyyy-MM-dd'T'HH:mm:ssX"), "ms", "yyyy-MM-dd HH:mm:ss") AS detected_time,
#             r.ruleClass AS rule_class,
#             [label IN LABELS(r) WHERE label <> 'Rule'][0] AS resource,
#             CASE
#                 WHEN r.level = 1 THEN ['LOW', 'success']
#                 WHEN r.level = 2 THEN ['MID', 'warning']
#                 WHEN r.level = 3 THEN ['HIGH', 'caution']
#                 ELSE ['CRITICAL', 'danger']
#             END AS level
#         ORDER BY detected_time DESC
#         """
#         results = self.run_data(database=self.user_db, query=cypher)
#         response = []
#         for result in results:
#             result = dict(result)
#             arr = {'account': account}
#             arr.update(result)
#             result.update({'arr': json.dumps(arr)})
#             response.append(result)
            
#         return response

#     # 사용자별 위협 분석
#     def get_user_visuals(self):
#         cypher = f"""
#         MATCH p = (r:Rule)<-[d:DETECTED|FLOW_DETECTED]-(l:Log)<-[:ACTED|DATE*]-(a:Account)
#         WITH DISTINCT(a), count(d) as count, COLLECT(r)[-1] as rule, COLLECT(l)[-1] as log
#         RETURN
#             HEAD([label IN LABELS(rule) WHERE label <> 'Rule']) AS resource,
#             CASE
#                 WHEN a.userName IS NOT NULL THEN a.userName
#                 WHEN a.name CONTAINS 'cgid' THEN SPLIT(a.name, '_')[0]
#                 ELSE a.name
#             END AS account,
#             CASE
#                 WHEN a.name CONTAINS 'cgid' THEN a.name
#                 ELSE '-'
#             END AS account_real,
#             count AS total,
#             rule.ruleName AS recent_detection,
#             log.eventName AS recent_action,
#             apoc.date.format(apoc.date.parse(log.eventTime, "ms", "yyyy-MM-dd'T'HH:mm:ssX"), "ms", "yyyy-MM-dd HH:mm:ss") AS recent_time
#         ORDER BY total DESC
#         """
#         results = self.run_data(database=self.user_db, query=cypher)
#         response = [result for result in results]
        
#         return response
    
#     def get_node_json(self, node:dict, cloud):
#         data = {
#             "id" : node.id,
#             "name" : "",
#             "score" : 400,
#             "query" : True,
#             "gene" : True
#         }
#         property_ = dict(node.items())
#         property_ = {key:property_[key] for key in sorted(property_.keys())}
#         if 'Log' in node.labels:
#             data['label'] = 'Log'
#             for key, value in property_.items():
#                 if key == 'eventName':
#                     data['name'] = value
#                 else:
#                     if any(x in key for x in ['responseElements','requestParameters','tls']):
#                         continue
#                     if 'userAgent' in key:
#                         continue
#                     if 'errorMessage' in key:
#                         value = value.replace('\'', '[',1)
#                         value = value.replace('\'', ']',1)
#                     if '\'' in str(value):
#                         value = value.replace('\'', '[',1)
#                         value = value.replace('\'', ']',1)
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
#                 property_ = dict(sorted(property_.items(), key=operator.itemgetter(1), reverse=True))
#             if 'Role' in node.labels:
#                 data['label'] = 'Role'
#             if 'Rule' in node.labels:
#                 data['label'] = 'Rule'
#                 data['name'] = property_['ruleName']
#             for key, value in property_.items():
#                 if key == 'name':
#                     value = str(value)
#                     value = value.split('_')[0]
#                 if any(x in key for x in ['responseElements','requestParameters','tls','query','ruleOperators', 'ruleValues','ruleKeys']):
#                     continue
#                 if 'errorMessage' in key:
#                     value = value.replace('\'', '[',1)
#                     value = value.replace('\'', ']',1)
#                 if key == 'date' or key == 'userName':
#                     value = str(value)
#                     data['name'] = value
#                 data[key] = value
#         response = {
#             "data": data,
#             "group" : "nodes"
#         }
#         return response

#     def get_relation_json(self, relation):
#         data = {
#             "source" : relation['start_node_id'],
#             "target" : relation['end_node_id'],
#             "weight" : 1,
#             "group" : "coexp",
#             "id" : "e"+str(relation['relation_id']),
#             "name": relation['relation_type']
#         }
#         response = {
#             "data" : data,
#             "group" : "edges"
#         }
        
#         return response
