# # local
# from common.neo4j.handler import Neo4jHandler
# # django
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

# class Default(Neo4jHandler):
#     def __init__(self, request) -> None:
#         super().__init__()
#         self.request = dict(request.POST.items()) if request.method == 'POST' else dict(request.GET.items())
#         self.user_db = request.session.get('db_name')
    
#     # List All Rules
#     def get_all_rules(self):
#         cypher = f"""
#         MATCH (r:RULE:AWS)
#         RETURN
#             id(r) as id,
#             HEAD([label IN labels(r) WHERE label <> 'RULE' AND label <> 'FLOW']) as label,
#             CASE
#                 WHEN 'FLOW' IN labels(r) THEN 'FLOW'
#                 ELSE split(r.eventSource, '.')[0]
#             END as log_type,
#             r.ruleName as name,
#             r.ruleComment as comment,
#             r.level as level,
#             r.on_off as on_off,
#             r.ruleType as rule_type
#         """
#         results = self.run_data(database=self.user_db, query=cypher)
#         response = {'rules': results}
#         return response

#     # List Default Rules
#     def get_default_rules(self, logType):
#         cypher= f"""
#         MATCH (r:Rule:{logType.split('_')[0].capitalize()} {{ruleType: 'default'}})
#         RETURN
#         id(r) as id,
#         CASE
#             WHEN r.ruleClass = 'dynamic' THEN 'Dynamic'
#             WHEN r.eventSource IS NULL THEN 'All'
#             WHEN r.ruleClass IS NULL OR r.ruleClass = 'static' THEN split(r.eventSource,'.')[0]
#             ELSE split(r.eventSource, '.')[0]
#         END as type,
#         r.ruleName as name,
#         r.ruleComment as comment,
#         CASE
#             WHEN r.level = 1 THEN ['LOW', 'success']
#             WHEN r.level = 2 THEN ['MID', 'warning']
#             WHEN r.level = 3 THEN ['HIGH', 'caution']
#             ELSE ['CRITICAL', 'danger']
#         END AS level,
#         r.on_off as on_off
#         """
#         results = self.run_data(database=self.user_db, query=cypher)
#         response = {'default': results}
#         return response

#     # List Custom Rules
#     def get_custom_rules(self, logType):
#         cypher= f"""
#         MATCH (r:Rule:{logType.split('_')[0].capitalize()} {{ruleType: 'custom'}})
#         RETURN
#         id(r) as id,
#         CASE
#             WHEN r.ruleClass = 'dynamic' THEN 'Dynamic'
#             WHEN r.eventSource IS NULL THEN 'All'
#             WHEN r.ruleClass IS NULL OR r.ruleClass = 'static' THEN split(r.eventSource,'.')[0]
#             ELSE split(r.eventSource, '.')[0]
#         END as type,
#         r.ruleName as name,
#         r.ruleComment as comment,
#         CASE
#             WHEN r.level = 1 THEN ['LOW', 'success']
#             WHEN r.level = 2 THEN ['MID', 'warning']
#             WHEN r.level = 3 THEN ['HIGH', 'caution']
#             ELSE ['CRITICAL', 'danger']
#         END AS level,
#         r.on_off as on_off
#         """
#         results = self.run_data(database=self.user_db, query=cypher)
#         response = {'custom': results}
#         return response

#     # Rule On Off
#     def rule_on_off(self):
#         logType = self.request['log_type'].split(' ')[0].capitalize()
#         rule_name = self.request['rule_name']
#         on_off = self.request['on_off']
#         cypher = f"""
#         MATCH (r:Rule:{logType} {{ruleName:'{rule_name}'}})
#         SET r.on_off = {abs(int(on_off)-1)}
#         RETURN r
#         """
#         self.run(database=self.user_db, query=cypher)
#         try:
#             if abs(int(on_off)-1) == 1:
#                 cypher = f"""
#                 MATCH (r:Rule:{logType} {{ruleName:'{rule_name}'}})
#                 SET r.status = 'Add'
#                 RETURN r
#                 """
#                 self.run(database=self.user_db, query=cypher)
#             else:
#                 cypher = f"""
#                 MATCH (r:Rule:{logType} {{ruleName:'{rule_name}'}})
#                 WITH ID(r) AS nodeId
#                 MERGE (d:Rule {{status:'Delete', nodeId: nodeId}})
#                 RETURN d
#                 """
#                 self.run(database=self.user_db, query=cypher)
#             return abs(int(on_off)-1)
#         except Exception as e:
#             print('Error: run_on_off()', e)
#             return int(2)

#     ## Rule Detail Modal
#     # List Rule Details
#     def get_rule_details(self, ruleType):
#         logType = self.request['log_type'].split(' ')[0].capitalize()
#         rule_name = self.request['rule_name']
#         cypher = f"""
#         MATCH (r:Rule:{logType} {{ruleName:'{rule_name}', ruleType:'{ruleType}'}})
#         RETURN
#             id(r) as id,
#             CASE
#                 WHEN r.ruleClass = 'dynamic' THEN 'Dynamic'
#                 WHEN r.eventSource IS NULL THEN 'All'
#                 WHEN r.ruleClass IS NULL OR r.ruleClass = 'static' THEN split(r.eventSource,'.')[0]
#                 ELSE split(r.eventSource, '.')[0]
#             END as type,
#             r
#         """
#         results = self.run_data(database=self.user_db, query=cypher)
#         response = {}
#         details = {}
#         filter = ['ruleType', 'ruleName', 'ruleComment', 'on_off', 'wheres']
#         filter += ['ruleKeys', 'ruleLogicals', 'ruleValues', 'ruleOperators']
#         for result in results:
#             rule_id = result['id']
#             response.update({'id': rule_id})
#             response.update({'type': result['type']})
#             for key, value in result['r'].items():
#                 if key == 'query': continue
#                 if key in filter:
#                     response.update({key:value})
#                     continue
#                 details.update({key.capitalize():value})
#         details = dict(sorted(details.items(), key=lambda x: x[0], reverse=False))
#         response.update({'details': details})
#         response['logType'] = logType
#         if response['type'] == 'Dynamic':
#             response.update(self.get_related_flow(logType, rule_name, rule_id))
#         return response

#     # Check And List Related Flow
#     def get_related_flow(self, logType, ruleName, rule_id):
#         cypher = f"""
#             MATCH (rule:Rule:{logType} {{ruleName: '{ruleName}'}})
#             WHERE ID(rule) = {rule_id}
#             UNWIND KEYS(rule) as key
#             WITH DISTINCT(key) as key, rule
#             WHERE key =~ 'flow.*'
#             WITH rule[key] as flowName
#             MATCH (flow:FLOW{{flowName:flowName}})
#             RETURN COLLECT(flow) as flows
#         """
#         results = self.run_data(database=self.user_db, query=cypher)
#         data = []
#         filter = ['flowName', 'flowComment']
#         for result in results:
#             for flow in result['flows']:
#                 rule = {}
#                 detail = {}
#                 for key, value in flow.items():
#                     if key in filter:
#                         rule.update({key:value})
#                     else:
#                         detail.update({key.capitalize():value})
#                 detail = dict(sorted(detail.items(), key=lambda x: x[0], reverse=False))
#                 rule.update({'detail': detail})
#                 data.append(rule)
#         response = {'related': data}
        
#         # << 최적화 코드. 추후 변경예정
#         # filter = ['flowName', 'flowComment']
#         # data = []

#         # for result in results:
#         #     for flow in result['flows']:
#         #         rule = {k: v for k, v in flow.items() if k in filter}
#         #         detail = {k.capitalize(): v for k, v in flow.items() if k not in filter}
#         #         rule['detail'] = dict(sorted(detail.items()))

#         # data.append(rule)
#         # response = {'related': data}
#         return response