# local
from datetime import datetime
from common.neo4j.handler import Neo4jHandler
import traceback
from ..models import Policy

# django
from django.conf import settings

## Graph DB 연동
host = settings.NEO4J['HOST']
port = settings.NEO4J["PORT"]
username = settings.NEO4J['USERNAME']
password = settings.NEO4J['PASSWORD']


class CompliancePolicyBase(Neo4jHandler):
    def __init__(self, request) -> None:
        super().__init__()
        self.request = dict(request.POST.items()) if request.method == 'POST' else dict(request.GET.items())
        self.user_db = request.session.get('db_name')


class CompliancePolicyHandler(CompliancePolicyBase):
    def get_policy_data_list(self):
        try:
            main_search_key = self.request.get('main_search_key', '')
            main_search_value = self.request.get('main_search_value', '')

            if main_search_key == 'policy' and main_search_value:
                cypher=f"""
                    MATCH (:Evidence:Compliance)-[:PRODUCT]->(:Product{{name:'Policy Manage'}})-[:POLICY]->(p:Policy)
                    WHERE toLower(p.name) CONTAINS toLower('{main_search_value}')
                    OPTIONAL MATCH (p)-[:DATA]->(d:Data:Evidence:Compliance)
                    RETURN p AS policy, COLLECT(d) AS data
                    ORDER BY policy.name ASC
                """
            elif main_search_key == 'data' and main_search_value:
                cypher=f"""
                    MATCH (:Evidence:Compliance)-[:PRODUCT]->(:Product{{name:'Policy Manage'}})-[:POLICY]->(p:Policy)
                    MATCH (p)-[:DATA]->(d:Data:Evidence:Compliance)
                    WHERE toLower(d.name) CONTAINS toLower('{main_search_value}')
                    RETURN p AS policy, COLLECT(d) AS data
                    ORDER BY policy.name ASC
                """
            else:
                cypher=f"""
                    MATCH (:Evidence:Compliance)-[:PRODUCT]->(:Product{{name:'Policy Manage'}})-[:POLICY]->(p:Policy)
                    OPTIONAL MATCH (p)-[:DATA]->(d:Data:Evidence:Compliance)
                    RETURN p AS policy, COLLECT(d) AS data
                    ORDER BY policy.name ASC
                """
            results = self.run_data(database=self.user_db, query=cypher)
            return results
        except Exception as e:
            print(f"Fail to CompliancePlicyBase Class in get_policy_data_list() -> {e}")
            return []

    def add_policy(self):
        try:
            policy = self.request.get('policy', None)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if not policy:
                return "Please Enter Policy Name"
            
            cypher = f"""
            MATCH (:Evidence:Compliance)-[:PRODUCT]->(:Product{{name:'Policy Manage'}})-[:POLICY]->(p:Policy {{name:'{policy}'}})
            RETURN COUNT(p) AS count
            """
            result = self.run(database=self.user_db, query=cypher)
            if 0 < result['count']:
                return "Policy Already Exists. Please Enter New Policy Name"
            else:
                cypher = f"""
                MATCH (:Evidence:Compliance)-[:PRODUCT]->(product:Product{{name:'Policy Manage'}})
                MERGE (p:Policy:Evidence:Compliance {{name:'{policy}', last_update:'{timestamp}'}})
                MERGE (product)-[:POLICY]->(p)
                """
                self.run(database=self.user_db, query=cypher)
                return "Successfully Created Policy"
        except Exception as e:
            return "Failed To Create Policy. Please Try Again."

    def modify_policy(self):
        try:
            og_policy = self.request.get('og_policy', '')
            policy = self.request.get('policy', '')
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if not og_policy:
                raise Exception
            if not policy:
                return "Please Enter Policy Name"
            
            cypher = f"""
            MATCH (:Evidence:Compliance)-[:PRODUCT]->(:Product{{name:'Policy Manage'}})-[:POLICY]->(p:Policy {{name:'{policy}'}})
            RETURN COUNT(p) AS count
            """
            result = self.run(database=self.user_db, query=cypher)
            if 0 < result['count']:
                return "Policy Already Exists. Please Enter New Policy Name"
            else:
                cypher = f"""
                MATCH (:Product{{name:'Policy Manage'}})-[:POLICY]->(p:Policy {{name:'{og_policy}'}})
                SET p.name = '{policy}',
                    p.last_update = '{timestamp}'
                """
                self.run(database=self.user_db, query=cypher)
                return "Successfully Modified Policy"
        except Exception as e:
            print(e)
            return "Failed To Modify Policy. Please Try Again."

    def delete_policy(self):
        try:
            policy = self.request.get('policy', None)
            if not policy:
                raise Exception
            else:
                cypher = f"""
                MATCH (:Product{{name:'Policy Manage'}})-[:POLICY]->(p:Policy {{name:'{policy}'}})
                OPTIONAL MATCH (p)-[:DATA]->(d:Data:Evidence:Compliance)
                OPTIONAL MATCH (d)-[:FILE]->(f:File:Evicence:Compliance)
                DETACH DELETE p
                DETACH DELETE d
                DETACH DELETE f
                """
                self.run(database=self.user_db, query=cypher)
                return 'Successfully Deleted Policy'
        except Exception as e:
            print(e)
            return 'Failed To Delete Policy. Please Try Again.'

    def add_policy_data(self):
        for key, value in self.request.items():
            if not value:
                return f"Please Enter/Select Data {key.title()}"
        try:
            policy = self.request.get('policy', '')
            name = self.request.get('name', '')
            comment = self.request.get('comment', '')
            author = self.request.get('author', '')
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cypher = f"""
            MATCH (:Product{{name:'Policy Manage'}})-[:POLICY]->(p:Policy {{name:'{policy}'}})-[:DATA]->(d:Data {{name:'{name}'}})
            RETURN COUNT(d) AS count
            """
            result = self.run(database=self.user_db, query=cypher)
            if 0 < result['count']:
                return "Policy Data Name Already Exists. Please Enter New Policy Data Name."
            else:
                cypher = f"""
                MATCH (:Product{{name:'Policy Manage'}})-[:POLICY]->(p:Policy {{name:'{policy}'}})
                MERGE (d:Data:Evidence:Compliance {{name:'{name}', comment:'{comment}', author:'{author}', last_update:'{timestamp}'}})
                MERGE (p)-[:DATA]->(d)
                """
                self.run(database=self.user_db, query=cypher)
                return "Successfully Added Policy Data"
        except Exception as e:
            print(e)
            return "Failed To Add Policy Data. Please Try Again."

    def modify_policy_data(self):
        for key, value in self.request.items():
            if not value and key not in ['og_name']:
                return f"Please Enter/Select Data {key.title()}"
        try:
            policy = self.request.get('policy', '')
            name = self.request.get('name', '')
            og_name = self.request.get('og_name', '')
            comment = self.request.get('comment', '')
            author = self.request.get('author', '')
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cypher = f"""
            MATCH (:Product{{name:'Policy Manage'}})-[:POLICY]->(p:Policy {{name:'{policy}'}})-[:DATA]->(d:Data {{name:'{name}'}})
            RETURN COUNT(d) AS count
            """
            result = self.run(database=self.user_db, query=cypher)
            
            if og_name != name and 0 < result['count']:
                return "Policy Data Name Already Exists. Please Enter New Policy Data Name."
            else:
                cypher = f"""
                MATCH (:Product{{name:'Policy Manage'}})-[:POLICY]->(p:Policy {{name:'{policy}'}})-[:DATA]->(d:Data {{name:'{og_name}'}})
                SET d.name = '{name}',
                    d.comment = '{comment}',
                    d.author = '{author}',
                    d.last_update = '{timestamp}'
                """
                self.run(database=self.user_db, query=cypher)
                
                return "Successfully Modified Policy Data"
        except Exception as e:
            print(e)
            
            return "Failed To Modify Policy Data. Please Try Again."

    def delete_policy_data(self):
        # for key, value in request.POST.dict().items():
        #     if not value:
        #         return f"Please Enter/Select Data {key.title()}"
        try:
            policy = self.request.get('policy', '')
            name = self.request.get('name', '')
            comment = self.request.get('comment', '')
            author = self.request.get('author', '')
            cypher = f"""
            MATCH (:Product{{name:'Policy Manage'}})-[:POLICY]->(p:Policy {{name:'{policy}'}})
            MATCH (p)-[:DATA]->(d:Data {{
                    name:'{name}',
                    comment:'{comment}',
                    author:'{author}'
                }})
            OPTIONAL MATCH (d)-[:FILES]->(f)
            RETURN COUNT(f) AS count_f, COUNT(d) AS count_d
            """
            
            results = self.run(database=self.user_db, query=cypher)
            if 0 < results['count_f']:
                cypher = f"""
                MATCH (:Product{{name:'Policy Manage'}})-[:POLICY]->(p:Policy {{name:'{policy}'}})
                MATCH (p)-[:DATA]->(d:Data {{
                        name:'{name}',
                        comment:'{comment}',
                        author:'{author}'
                    }})
                OPTIONAL MATCH (d)-[:FILES]->(f)
                RETURN {{name: f.name, comment: f.commnet}} AS file
                """
                results = self.run_data(database=self.user_db, query=cypher)
                return "test" # <<<<?
            
            if 0 < results['count_d']:
                cypher = f"""
                MATCH (:Product{{name:'Policy Manage'}})-[:POLICY]->(p:Policy {{name:'{policy}'}})
                MATCH (p)-[:DATA]->(d:Data {{
                        name:'{name}',
                        comment:'{comment}',
                        author:'{author}'
                    }})
                OPTIONAL MATCH (d)-[:FILES]->(f)
                DETACH DELETE d
                RETURN {{name: f.name, comment: f.commnet}} AS file
                """
                self.run(database=self.user_db, query=cypher)
                return "Successfully Deleted Policy Data"
            else:
                raise Exception

        except Exception as e:
            print(traceback.format_exc())
            return "Failed To Delete Policy Data. Please Try Again."

    def get_policy_data_details(self, policy_type, data_type):
        try:
            if not policy_type or not data_type:
                raise Exception
            else:
                cypher = f"""
                MATCH (:Evidence:Compliance)-[:PRODUCT]->(:Product{{name:'Policy Manage'}})-[:POLICY]->(policy:Policy{{name:'{policy_type}'}})-[:DATA]->(data:Data:Evidence{{name:'{data_type}'}})
                RETURN data AS data
                """
                data_result = self.run(database=self.user_db, query=cypher)
                
                cypher = f"""
                MATCH (:Evidence:Compliance)-[:PRODUCT]->(:Product{{name:'Policy Manage'}})-[:POLICY]->(policy:Policy{{name:'{policy_type}'}})-[:DATA]->(data:Data:Evidence{{name:'{data_type}'}})
                MATCH (data)-[:FILE]->(file)
                RETURN COLLECT(file) AS file
                """
                file_result = self.run(database=self.user_db, query=cypher)

                return {'data': data_result['data'],  
                        'file_list': file_result['file']}
                
        except Exception as e:
            print(e)
            return {'data':{},
                    'file_list':[]}


class PolicyFileHandler(Neo4jHandler):
    def __init__(self, request) -> None:
        super().__init__()
        self.request = request
        self.request_data = dict(request.POST.items()) if request.method == 'POST' else dict(request.GET.items())
        self.user_db = request.session.get('db_name')
        self.user_uuid = request.session.get('uuid')
        
        
    def add_policy_data_file(self):
        for key, value in self.request_data.items():
            if not value:
                return f"Please Enter/Select Data {key.title()}"
        try:
            file = self.request.FILES.get('file', '')
            file_name = file.name.replace(' ', '_')
            print(f"file name: {file_name}")
            
            cypher = f"""
            MATCH (f:File:Compliance:Evidence {{name:'{file_name}'}})
            RETURN COUNT(f) AS count
            """
            result = self.run(database=self.user_db, query=cypher)
            if 0 < result['count']:
                return "Data File Already Exsists. Please Select New File"
            else:
                policy = self.request_data.get('policy', '')
                name = self.request_data.get('name', '')
                comment = self.request_data.get('comment', '')
                author = self.request_data.get('author', '')
                version = self.request_data.get('version', '')
                poc = self.request_data.get('poc', '')
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                cypher = f"""
                MATCH (:Evidence:Compliance)-[:PRODUCT]->(:Product{{name:'Policy Manage'}})-[:POLICY]->(p:Policy{{name:'{policy}'}})-[:DATA]->(d:Data:Evidence{{name:'{name}'}})
                MERGE (f:File:Compliance:Evidence {{
                        name:'{file_name}',
                        comment:'{comment}',
                        author:'{author}',
                        version:'{version}',
                        poc:'{poc}',
                        upload_date:'{timestamp}',
                        last_update: '{timestamp}'
                    }})
                MERGE (d)-[:FILE]->(f)
                SET d.last_update = '{timestamp}'
                """
                self.run(database=self.user_db, query=cypher)
                
                # 디비에 파일 정보 저장
                document = Policy(
                    user_uuid=self.user_uuid,
                    title=comment,
                    uploadedFile=file
                )
                document.save()
                return "Successfully Added Policy Data File"
        except Exception as e:
            print(e)
            return "Failed To Add Policy Data File. Please Try Again."

    def modify_policy_data_file(self):
        for key, value in self.request_data.items():
            if not value:
                return f"Please Enter/Select {key.capitalize()}"
        try:
            policy = self.request_data.get('policy', '')
            data_name = self.request_data.get('name', '')
            file_name = self.request_data.get('file', '')
            comment = self.request_data.get('comment', '')
            og_comment = self.request_data.get('og_comment', '')
            author = self.request_data.get('author', '')
            version = self.request_data.get('version', '')
            poc = self.request_data.get('poc', '')
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cypher = f"""
            
            RETURN COUNT(f) AS count
            """
            result = self.run(database=self.user_db, query=cypher)
            
            if 0 < result['count']:
                cypher = f"""
                MATCH (:Evidence:Compliance)-[:PRODUCT]->(:Product{{name:'Policy Manage'}})-[:POLICY]->(p:Policy{{name:'{policy}'}})-[:DATA]->(d:Data:Evidence{{name:'{data_name}'}})
                MATCH (d)-[:FILE]->(f:File:Evidence:Compliance{{name:'{file_name}'}})
                SET f.comment = '{comment}', 
                    f.author = '{author}', 
                    f.version = '{version}',
                    f.poc = '{poc}',
                    f.last_update = '{timestamp}',
                    d.last_update = '{timestamp}'
                """
                self.run(database=self.user_db, query=cypher)
                if og_comment != comment:
                    documents = Policy.objects.filter(user_uuid=self.user_uuid, title=f"{og_comment}")
                    for document in documents:
                        if document.uploadedFile.name.endswith(file_name.replace('[','').replace(']','')):
                            document.title = comment
                            document.save()
                            print('modified')
                return "Successfully Modified Policy Data File"
            else:
                raise Exception
        except Exception as e:
            print(e)
            return "Failed To Modify Policy Data File. Please Try Again."

    def delete_policy_data_file(self):
        try:
            policy = self.request_data.get('policy', '')
            data_name = self.request_data.get('name', '')
            file_name = self.request_data.get('file', '')
            comment = self.request_data.get('comment', '')
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cypher = f"""
            MATCH (:Evidence:Compliance)-[:PRODUCT]->(:Product{{name:'Policy Manage'}})-[:POLICY]->(p:Policy{{name:'{policy}'}})-[:DATA]->(d:Data:Evidence{{name:'{data_name}'}})
            MATCH (d)-[:FILE]->(f:File:Evidence:Compliance{{
                name:'{file_name}',
                comment:'{comment}'
            }})
            RETURN COUNT(f) AS count
            """
            result = self.run(database=self.user_db, query=cypher)
            
            if 0 < result['count']:
                cypher = f"""
                MATCH (:Evidence:Compliance)-[:PRODUCT]->(:Product{{name:'Policy Manage'}})-[:POLICY]->(p:Policy{{name:'{policy}'}})-[:DATA]->(d:Data:Evidence{{name:'{data_name}'}})
                MATCH (d)-[:FILE]->(f:File:Evidence:Compliance{{
                    name:'{file_name}',
                    comment:'{comment}'
                }})
                DETACH DELETE f SET d.last_update = '{timestamp}'
                """
                self.run(database=self.user_db, query=cypher)
                documents = Policy.objects.filter(user_uuid=self.user_uuid, title=comment)
                for document in documents:
                    if document.uploadedFile.name.endswith(file_name.replace('[','').replace(']','')):
                        print(document.uploadedFile.path)
                        document.uploadedFile.delete(save=False)
                        document.delete()
                return "Successfully Deleted Policy Data File"
            else:
                raise Exception
        except Exception as e:
            print(e)
            return "Failed To Delete Policy Data File. Please Try Again."
