# # local
# from datetime import datetime
# import traceback
# # 3rd party
# from neo4j import GraphDatabase
# # django
# from django.conf import settings

# NEO4J_URI = f"bolt://{settings.NEO4J['HOST']}:{settings.NEO4J['PORT']}"
# username = settings.NEO4J['USERNAME']
# password = settings.NEO4J['PASSWORD']

# class Neo4jHandler:
#     def __init__(self) -> None:
#         self.uri = f"bolt://{settings.NEO4J['HOST']}:{settings.NEO4J['PORT']}"
#         self.user = settings.NEO4J['USERNAME']
#         self.pw = settings.NEO4J['PASSWORD']
        
#         self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.pw))
        
#     def __enter__(self):
#         return self
    
#     def __exit__(self, exc_type, exc_value, traceback):
#         self.close()
        
#     def close(self):
#         self.driver.close()
    
#     def run(self, database, query):
#         """Execute run cypher and returns a single result.

#         Args:
#             database (str): The user's neo4j database address.
#             query (str): Cypher query
        
#         Example:
#             >>> "MATCH (n) RETURN COUNT(n) AS count"
#             >>> result = self.run(database=self.user_db, query=query)
#             >>> result['count'], type(result['count'])
#                 5 int

#         Returns:
#             list: [<dict|Record>, <dict|Record>, ...]
#         """
#         try:
#             with self.driver.session(database=database) as session:
#                 res = session.execute_write(self._run, query)
#                 return res
#         except:
#             print(traceback.format_exc())
    
#     def run_records(self, database, query) -> list:
#         """Execute run cypher and returns a list of multiple record objects.

#         Args:
#             database (str): The user's neo4j database address.
#             query (str): Cypher query
        
#         Example:
#             >>> results = self.run_records(database=self.user_db, query=query)
#             [{Record id: 1, ...}, 
#             {Record id: 2, ...}]

#         Returns:
#             list: [<dict|Record>, <dict|Record>, ...]
#         """
#         with self.driver.session(database=database) as session:
#             res = session.execute_write(self._run_records, query)
#             return res
    
#     def run_data(self, database, query) -> list:
#         """Execute run cypher and returns a list of multiple dict objects.

#         Args:
#             database (str): The user's neo4j database address.
#             query (str): Cypher query
        
#         Example:
#             >>> results = self.run_data(database=self.user_db, query=query)
#                 [{'id': 1, 'name': 'admin'}, 
#                 {'id': 2, 'name': 'yoonan'}]

#         Returns:
#             list: [<dict>, <dict>, ...]
#         """
#         with self.driver.session(database=database) as session:
#             res = session.execute_write(self._run_records, query)
#             return res
        
#     def create_database(self, db_name):
#         query = f"CREATE DATABASE `{db_name}`"
#         with self.driver.session() as session:
#             session.execute_write(self._run, query)
#         self.close()
    
#     @staticmethod
#     def _run(tx, query):
#         res = tx.run(query)
#         record = res.single()
        
#         return record if record else None
    
#     @staticmethod
#     def _run_records(tx, query) -> list:
#         res = tx.run(query)
#         return list(res)
    
#     @staticmethod
#     def _run_data(tx, query) -> dict:
#         res = tx.run(query)
#         return [record.data() for record in res]
# neo4j_handler = Neo4jHandler()


# class Cypher(Neo4jHandler):
#     def __init__(self) -> None:
#         super().__init__()
    
#     def close(self):
#         Neo4jHandler.close(self)
        
#     def push_user(self, user, ip):
#         query = f"""
#         MERGE (super:Super:Teiren {{name:'Teiren'}})
#         WITH super
#         MERGE (super)-[:SUB]->(a:Teiren:Account {{
#             userName: '{user.username}',
#             userPassword: '{user.password}',
#             email: '{user.email}',
#             createdTime: '{str(datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))}',
#             ipAddress: '{ip}',
#             uuid: '{user.uuid}',
#             failCount: 0,
#             emailCheck: 'False'
#         }})
#         RETURN ID(a) as id
#         """
#         res = Neo4jHandler.run(self, user.db_name, query)
#         return res
# cypherhandler = Cypher()