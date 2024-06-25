import re
from django.conf import settings
from datetime import datetime
from ..models import Evidence
import traceback

from common.neo4j.handler import Neo4jHandler

## Graph DB 연동
host = settings.NEO4J['HOST']
port = settings.NEO4J["PORT"]
username = settings.NEO4J['USERNAME']
password = settings.NEO4J['PASSWORD']


class EvidenceBase(Neo4jHandler):
    """_summary_
    
    Args:
        request : request from session
    
    Example:
        >>> def __init__(self, request) -> None:
        >>>     super().__init__()
        >>>     self.request = dict(request.POST) if request.method == 'POST' else dict(request.GET.items())
        >>>     self.user_db = request.session.get('db_name')
         
    """
    def __init__(self, request) -> None:
        super().__init__()
        self.request = dict(request.POST.items()) if request.method == 'POST' else dict(request.GET.items())
        self.user_db = request.session.get('db_name')


class EvidenceDataList(EvidenceBase):
    # data 목록 가져오기
    def get_data_list(self, data_name=None):
        try:
            main_search_key = self.request.get('main_search_key', '')
            main_search_value = self.request.get('main_search_value', '')
            
            if data_name:
                cypher = f"""
                MATCH (p:Product:Evidence:Compliance)-[:DATA]->(d:Data:Compliance:Evidence)
                WHERE NOT p.name ENDS WITH "Manage" AND d.name = '{data_name}'
                RETURN d AS data, p AS product
                """
            elif not main_search_key or not main_search_value:
                cypher= f"""
                MATCH (p:Product:Evidence:Compliance)-[:DATA]->(d:Data:Compliance:Evidence)
                WHERE NOT p.name ENDS WITH "Manage"
                RETURN d AS data, p AS product
                """
            else:
                cypher = f"""
                MATCH (p:Product:Evidence:Compliance)-[:DATA]->(d:Data:Compliance:Evidence)
                WHERE NOT p.name ENDS WITH "Manage" AND toLower(d.{main_search_key}) CONTAINS toLower('{main_search_value}')
                RETURN d AS data, p AS product
                """
            results = self.run_data(database=self.user_db, query=cypher)
            
            return results
        except Exception as e:
            return []

    def get_product_list(self):
        try:
            cypher = """
            MATCH (p:Product:Evidence:Compliance)
            WHERE NOT p.name ENDS WITH "Manage"
            WITH p.name as product ORDER BY p.name
            RETURN COLLECT(product) AS product
            """
            result = self.run(database=self.user_db, query=cypher)
            
            return result['product']
        except Exception as e:
            return []

    def get_compliance_list(self):
        try:
            cypher = f"""
            MATCH (:Compliance)-[:COMPLIANCE]->(c:Compliance)
            WHERE c.name <> 'Evidence'
            WITH replace(toUpper(c.name), '_', '-') as compliance ORDER BY c.name
            RETURN COLLECT(compliance) AS compliance
            """
            result = self.run(database=self.user_db, query=cypher)
            
            return result['compliance']
        except Exception as e:
            return []

    def get_file_list(self, data_name):
        try:
            cypher = f"""
            MATCH (d:Data:Compliance:Evidence{{name:'{data_name}'}})-[:FILE]->(file:File:Compliance:Evidence)
            RETURN collect(file) AS file
            """
            result = self.run(database=self.user_db, query=cypher)
            
            return result['file']
        except Exception as e:
            return []

    def get_data_related_compliance(self, search_cate=None, search_content=None) -> dict:
        try:
            if search_cate=="compliance":
                cypher=f"""
                MATCH (com:Compliance{{name:'{search_content}'}})-[:VERSION]->(ver:Version)-[:CHAPTER]->(chap:Chapter)-[:SECTION]->(sec:Section)-[:ARTICLE]->(arti:Article)
                RETURN com, ver, chap, sec, arti ORDER BY arti.no
                """
            elif search_cate=="evidence":
                cypher=f"""
                MATCH (version:Version:Compliance)-[:CHAPTER]->(chapter:Chapter)-[:SECTION]->(section:Section)-[:ARTICLE]->(article:Article)<-[:EVIDENCE]-(evi:Data:Compliance:Evidence{{name:'{search_content}'}})
                RETURN version, chapter, section, article ORDER BY article.no

                UNION

                MATCH (version:Version:Compliance)-[:CHAPTER]->(chapter:Chapter)-[:ARTICLE]->(article:Article)<-[:EVIDENCE]-(evi:Data:Compliance:Evidence{{name:'{search_content}'}})
                RETURN version, chapter, '' AS section, article ORDER BY article.no

                UNION

                MATCH (version:Version:Compliance)-[:ARTICLE]->(article:Article)<-[:EVIDENCE]-(evi:Data:Compliance:Evidence{{name:'{search_content}'}})
                RETURN version, '' AS chapter, '' AS section, article ORDER BY article.no

                UNION

                MATCH (version:Version:Compliance)<-[:EVIDENCE]-(evi:Data:Compliance:Evidence{{name:'{search_content}'}})
                RETURN version, '' AS chapter, '' AS section, '' AS article
                """
            results = self.run_data(database=self.user_db, query=cypher)
            compliance_list = list()
            for result in results:
                compliance_list.append(dict(result))
            
            return compliance_list
        except Exception as e:
            return []


class EvidenceDataHandler(EvidenceBase):
    # data 추가
    def add_evidence_data(self):
        for key, value in self.request.items():
            if value == '' and key not in ['comment', 'author', ''] :
                return f"Please Enter/Select {key.title()}"
        try:
            last_update = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cypher = f"""
            MATCH (c:Data:Compliance:Evidence{{
                name:'{self.request['name']}'
            }})
            RETURN count(c) AS count
            """
            result = self.run(database=self.user_db, query=cypher)
            if 0 < result['count']:
                return "Data Already Exsists. Please Enter Different Name."
            else:
                if self.request['article'] != '':
                    cypher = f"""
                    MATCH (e:Compliance:Evidence{{name:'Evidence'}})-[:PRODUCT]->(p:Product:Evidence{{name:'{self.request['product']}'}})
                    MATCH (v:Version{{name:'{self.request['compliance'].replace('-','_').capitalize()}', date:date('{self.request['version']}')}})-[*]->(a:Article{{compliance_name:'{self.request['compliance'].replace('-','_').capitalize()}', no:'{self.request['article'].split(' ')[0]}'}})
                    MERGE (p)-[:DATA]->
                        (d:Data:Compliance:Evidence {{
                        name:'{self.request['name']}',
                        comment:'{self.request['comment']}',
                        author:'{self.request['author']}',
                        last_update:'{last_update}'
                    }})-[:EVIDENCE]->(a)
                    RETURN COUNT(d) AS count
                    """
                elif self.request['compliance'] != '':
                    cypher = f"""
                    MATCH (e:Compliance:Evidence{{name:'Evidence'}})-[:PRODUCT]->(p:Product:Evidence{{name:'{self.request['product']}'}})
                    MATCH (c:Version:Compliance{{name:'{self.request['compliance'].replace('-','_').capitalize()}', date:date('{self.request['version']}')}})
                    MERGE (p)-[:DATA]->
                        (d:Data:Compliance:Evidence {{
                        name:'{self.request['name']}',
                        comment:'{self.request['comment']}',
                        author:'{self.request['author']}',
                        last_update:'{last_update}'
                    }})-[:EVIDENCE]->(c)
                    RETURN COUNT(d) AS count
                    """
                else:
                    raise Exception
                
                result = self.run(database=self.user_db, query=cypher)
                if 0 == result['count']:
                    raise Exception
                else:
                    return "Successfully Create Data."
        except Exception as e:
            print(e)
            return "Failed To Create Data. Please Try Again."

    def modify_evidence_data(self):
        try:
            og_name=self.request.get('og_name', '')
            name = self.request.get('name', '')
            
            cypher = f"""
            MATCH (c:Data:Compliance:Evidence{{
                name:'{name}'
            }})
            RETURN count(c) AS count
            """
            result = self.run(database=self.user_db, query=cypher)
            if not name:
                return "Please Enter Data Name"
            elif not og_name:
                raise Exception
            elif og_name != name and 0 < result['count']:
                return "Data Name Already Exsists. Please Enter New Data Name."
            else:
                comment = self.request.get('comment', '')
                author = self.request.get('author', '')
                
                last_update = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cypher = f"""
                MATCH (d:Data:Compliance{{name:'{og_name}'}})
                SET d.name = '{name}',
                    d.comment='{comment}',
                    d.author='{author}',
                    d.last_update='{last_update}' 
                RETURN COUNT(d) AS count
                """
                self.run(database=self.user_db, query=cypher)
                return "Successfully Modified Data"
        except Exception as e:
            print(e)
            return 'Failed To Modify Data. Please Try Again.'

    def delete_evidence_data(self):
        try:
            name = self.request.get('name', '')
            comment = self.request.get('comment', '')
            author = self.request.get('author', '')
            
            cypher = f"""
            MATCH (d:Compliance:Evidence:Data{{name:'{name}', comment:'{comment}', author:'{author}'}})
            OPTIONAL MATCH (d)-[:FILE]->(f:File:Compliance:Evidence)
            RETURN COUNT(f) AS count
            """
            result = self.run(database=self.user_db, query=cypher)
            
            if not name:
                raise Exception
            elif 0 < result['count']:
                return f"There Are Files In [ {name} ] Data. Please Try After Deleting The Files."

            cypher= f"""
            MATCH (d:Compliance:Evidence:Data{{name:'{name}', comment:'{comment}', author:'{author}'}})
            DETACH DELETE d
            """
            self.run(database=self.user_db, query=cypher)
            
            return "Successfully Deleted Data"
        except Exception as e:
            print(e)
            return "Failed To Delete Data. Please Try Again."

    def get_compliance_version_list(self):
        try:
            compliance = self.request.get('compliance', '').replace('-', '_').capitalize()
            cypher = f"""
            MATCH (:Compliance)-[:COMPLIANCE]->(c:Compliance{{name:'{compliance}'}})-[:VERSION]->(v:Version)
            WITH toString(v.date) as version ORDER BY v.date
            RETURN COLLECT(version)
            """
            response = self.run(database=self.user_db, query=cypher)
        except Exception as e:
            response = []
        finally:
            return response
    
    def get_compliance_article_list(self):
        try:
            compliance = self.request.get('compliance', '').replace('-', '_').capitalize()
            version = self.request.get('version', '')
            cypher=f"""
                OPTIONAL MATCH (c:Compliance{{name:'{compliance}'}})-[:VERSION]->(v:Version)-[:CHAPTER]->(:Chapter)-[:SECTION]->(:Section)-[:ARTICLE]->(a:Article)
                WITH a
                WHERE a IS NOT NULL AND v.date = date('{version}')
                RETURN a.no AS no, a.name AS name

                UNION

                OPTIONAL MATCH (c:Compliance{{name:'{compliance}'}})-[:VERSION]->(v:Version)-[:CHAPTER]->(:Chapter)-[:ARTICLE]->(a:Article)
                WITH a
                WHERE a IS NOT NULL AND v.date = date('{version}')
                RETURN a.no AS no, a.name AS name

                UNION

                OPTIONAL MATCH (c:Compliance{{name:'{compliance}'}})-[:VERSION]->(v:Version)-[:ARTICLE]->(a:Article)
                WITH a
                WHERE a IS NOT NULL AND v.date = date('{version}')
                RETURN a.no AS no, a.name AS name
            """
            response = []
            results = self.run_records(database=self.user_db, query=cypher)
            for result in results:
                response.append({'no':result['no'], 'name': result['name']})
            response = sorted(response, key=lambda x: [int(i) for i in x['no'].split('.')])
        except Exception as e:
            print(traceback.format_exc())
            response = []
        finally:
            return response

class EvidenceFileHandler(Neo4jHandler):
    def __init__(self, request) -> None:
        super().__init__()
        self.request = request
        self.request_data = dict(request.POST.items()) if request.method == 'POST' else dict(request.GET.items())
        self.user_db = request.session.get('db_name')
        self.user_uuid = request.session.get('uuid')
        
    def add_evidence_file(self):
        for key, value in self.request_data.items():
            if not value:
                return f"Please Enter/Select {key.capitalize()}"
        try:
            data_name = self.request_data.get('data_name', '')
            uploaded_file = self.request.FILES.get("file", '')
            product = self.request_data.get('product', '')
            file_name = re.sub(r'\s+', '_', uploaded_file.name)
            
            cypher = f"""
            MATCH (p:Product:Evidence:Compliance{{name:'{product}'}})-[*]->(f:File:Evidence:Compliance{{name:'{file_name}'}})
            RETURN count(f) AS count
            """
            result = self.run(database=self.user_db, query=cypher)
            if 0 < result['count']:
                return "File Name Already Exsists. Please Enter New File Name."
            else:
                comment = self.request_data.get('comment', '')
                author = self.request_data.get('author', '')
                version = self.request_data.get('version', '')
                poc = self.request_data.get('poc', '')
                upload_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Saving the information in the database
                document = Evidence(
                    user_uuid=self.user_uuid,
                    title=comment,
                    product=product,
                    uploadedFile=uploaded_file
                )
                document.save()
                
                cypher = f"""
                MATCH (d:Data:Compliance:Evidence{{name:'{data_name}'}})
                MERGE (f:File:Compliance:Evidence {{
                    name:'{file_name}',
                    comment:'{comment}',
                    author:'{author}',
                    poc:'{poc}',
                    version:'{version}',
                    upload_date:'{upload_date}'
                }})
                MERGE (d)-[:FILE]->(f)
                SET d.last_update='{upload_date}'
                """
                self.run(database=self.user_db, query=cypher)

                return "Successfully Added Evidence File"
        except Exception as e:
            print(traceback.format_exc())
            return 'Failed To Add Evidence File. Please Try Again.'

    def modify_evidence_file(self):
        for key, value in self.request_data.items():
            if not value:
                return f"Please Enter/Select {key.capitalize()}"
        try:
            data_name = self.request_data.get('data_name', '')
            name = self.request_data.get('name', '')
            comment = self.request_data.get('comment', '')
            og_comment = self.request_data.get('og_comment', '')
            author = self.request_data.get('author', '')
            version = self.request_data.get('version', '')
            poc = self.request_data.get('poc', '')
            
            last_update = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cypher = f"""
            MATCH (d:Data:Compliance{{name:'{data_name}'}})-[:FILE]->(f:File:Evidence:Compliance{{name:'{name}'}})
            SET f.comment='{comment}', 
                f.author='{author}', 
                f.version='{version}',
                f.poc='{poc}',
                f.last_update='{last_update}',
                d.last_update='{last_update}'
            """
            self.run(database=self.user_db, query=cypher)

            if og_comment != comment:
                documents = Evidence.objects.filter(user_uuid=self.user_uuid, title=f"{og_comment}")
                for document in documents:
                    if document.uploadedFile.name.endswith(name.replace('[','').replace(']','')):
                        document.title = comment
                        document.save()

            return "Successfully Modified Evidence File"
        except Exception as e:
            print(e)
            return "Failed To Modify Evidence File"

    def delete_evidence_file(self):
        try:
            data_name = self.request_data.get('data_name', '')
            name = self.request_data.get('name', '')
            comment = self.request_data.get('comment', '')
            author = self.request_data.get('author', '')
            version = self.request_data.get('version', '')
            poc = self.request_data.get('poc', '')
            upload_date = self.request_data.get('upload_date', '')
            last_update = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cypher = f"""
            MATCH (d:Data:Compliance:Evidence{{name:'{data_name}'}})-[:FILE]->
                (f:File:Evidence {{
                    name:'{name}',
                    comment:'{comment}',
                    author:'{author}',
                    poc:'{poc}',
                    version:'{version}',
                    upload_date: '{upload_date}'
                }})
            DETACH DELETE f
            SET d.last_update='{last_update}'
            """
            self.run(database=self.user_db, query=cypher)
            
            documents = Evidence.objects.filter(user_uuid=self.user_uuid, title=comment)
            for document in documents:
                if document.uploadedFile.name.endswith(name.replace('[','').replace(']','')):
                    # print(document.uploadedFile.path)
                    document.uploadedFile.delete(save=False)
                    document.delete()
            return "Successfully Deleted Evidence File"
        except Exception as e:
            print(e)
            return "Failed To Delete Evidence File"


class ComplianceHandler(EvidenceBase):
    def add_related_compliance(self):
        try:
            data_name = self.request.get('data_name', '')
            compliance = self.request.get('compliance', '')
            version = self.request.get('version', '')
            article = self.request.get('article', '')
            
            last_update = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if article:
                cypher= f"""
                MATCH (d:Data:Compliance:Evidence{{name:'{data_name}'}})
                MATCH (a:Article:Compliance{{compliance_name:'{compliance.replace('-','_').capitalize()}', no:'{article.split(' ')[0]}'}})
                MERGE (d)-[:EVIDENCE]->(a)
                SET d.last_update='{last_update}'
                RETURN COUNT(d)
                """
            elif compliance:
                cypher= f"""
                MATCH (d:Data:Compliance:Evidence{{name:'{data_name}'}})
                MATCH (v:Version:Compliance{{name:'{compliance.replace('-','_').capitalize()}', date:date('{version}')}})
                MERGE (d)-[:EVIDENCE]->(v)
                SET d.last_update='{last_update}'
                RETURN COUNT(d)
                """
            self.run(database=self.user_db, query=cypher)
            return "Successfully Added Related Complicance"
        except Exception as e:
            print(e)
            return "Failed To Add Related Complicance. Please Try Again."

    def delete_related_compliance(self):
        try:
            data_name = self.request.get('data_name', '')
            compliance = self.request.get('compliance', '')
            version = self.request.get('version', '')
            article = self.request.get('article', '')
            
            last_update = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if article and article != ' ':
                cypher= f"""
                MATCH (d:Data:Compliance:Evidence{{name:'{data_name}'}})
                MATCH (a:Article:Compliance{{compliance_name:'{compliance.replace('-','_').capitalize()}', no:'{article.split(' ')[0]}'}})
                MATCH (d)-[evidence:EVIDENCE]->(a)
                SET d.last_update='{last_update}'
                DELETE evidence
                """
            elif compliance:
                cypher= f"""
                MATCH (d:Data:Compliance:Evidence{{name:'{data_name}'}})
                MATCH (v:Version:Compliance{{name:'{compliance.replace('-','_').capitalize()}', date:date('{version}')}})
                MATCH (d)-[evidence:EVIDENCE]->(v)
                SET d.last_update='{last_update}'
                DELETE evidence
                """
            self.run(database=self.user_db, query=cypher)
            return "Successfully Deleted Related Complicance"
        except Exception as e:
            print(e)
            return "Failed To Delete Related Complicance. Please Try Again."