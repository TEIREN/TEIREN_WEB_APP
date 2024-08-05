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


# class Delete(Neo4jHandler):
#     def __init__(self, request) -> None:
#         super().__init__()
#         self.request = dict(request.POST.items()) if request.method == 'POST' else dict(request.GET.items())
#         self.user_db = request.session.get('db_name')
    
#     # Delete Rule Action
#     def delete_rule(self):
#         if self.request['ruleClass'] == 'Dynamic':
#             if isinstance(delete_check:=self.delete_dynamic_rule(self.request),str):
#                 return delete_check
#         else:
#             if isinstance(delete_check:=self.delete_static_rule(self.request),str):
#                 return delete_check
#         return 'Deleted Successfully'

#     def delete_static_rule(self, request):
#         logType = request['log_type']
#         ruleName = request['og_rule_name'] if 'og_rule_name' in request else request['rule_name']
#         cypher = f"""
#         MATCH (rule:Rule:{logType} {{ruleName:'{ruleName}'}})
#         DETACH DELETE rule
#         RETURN ID(rule) AS id
#         """
        
#         try:
#             result = self.run(database=self.user_db, query=cypher)
#             cypher = f"MERGE (r:Rule {{status: 'Delete', nodeId:{result['id']}}})"
#             self.run(database=self.user_db, query=cypher)
#             return {
#                 'status': 'success',
#                 'message': 'Success to Modify Rule'
#             }
#         except:
#             return 'Failed To Delete. Please Try Again'

#     def delete_dynamic_rule(self, request):
#         logType = request['log_type']
#         ruleName = request['og_rule_name'] if 'og_rule_name' in request else request['rule_name']
#         cypher = f"""
#         MATCH (rule:Rule:{logType} {{ruleName:'{ruleName}'}})
#         UNWIND KEYS(rule) as keys
#         WITH rule, keys
#         WHERE keys =~ 'flow.*'
#         WITH rule, rule[keys] as flowName
#         MATCH (flow:Flow{{flowName:flowName}})
#         WITH rule, flow
#         OPTIONAL MATCH (rule)<-[:FLOW_DETECTED]-(log:Log)
#         WITH rule, flow, log
#         CALL apoc.do.when(
#             log IS NOT NULL,
#             "
#                 OPTIONAL MATCH (log)<-[flow_rel:FLOW*]-(:Log)
#                 WITH CASE WHEN flow_rel IS NULL THEN [] ELSE flow_rel END AS flow_rel
#                 RETURN flow_rel AS flow_rel
#             ",
#             "
#                 RETURN [] AS flow_rel
#             ",
#             {{log:log}}
#         )YIELD value
#         WITH rule, flow, value.flow_rel as flow_rels
#         CALL apoc.do.when(
#             SIZE(flow_rels) > 0,
#             "
#                 UNWIND flow_rels as flow_rel
#                 DELETE flow_rel
#             ",
#             "
#                 RETURN 0
#             ",
#             {{flow_rels:flow_rels}}
#         )YIELD value
#         DETACH DELETE rule, flow
#         RETURN ID(rule) AS id
#         """
#         try:
#             result = self.run(database=self.user_db, query=cypher)
#             cypher = f"MERGE (r:Rule {{status: 'Delete', nodeId:{result['id']}}})"
#             self.run(database=self.user_db, query=cypher)
#             return {
#                 'status': 'success',
#                 'message': 'Success to Modify Rule'
#             }
#         except:
#             return 'Failed To Delete. Please Try Again'
    

