# local
import os
from datetime import datetime
from ..models import Asset
from common.neo4j.handler import Neo4jHandler
# django
from django.conf import settings
# 3rd party
from py2neo import Graph

## Graph DB 연동
host = settings.NEO4J['HOST']
port = settings.NEO4J["PORT"]
username = settings.NEO4J['USERNAME']
password = settings.NEO4J['PASSWORD']


class AssetsBase(Neo4jHandler):
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
        self.user_uuid = request.session.get('uuid')
    

class AssetListAction(AssetsBase):
    # Asset List
    def get_asset_list(self, asset_type):
        get_asset_cypher = f"""
        MATCH (c:Evidence:Compliance:Product{{name:'Asset Manage'}})-[:DATA]->(n:Evidence:Compliance:Data{{name:'{asset_type}', product:'Asset Manage'}})
        OPTIONAL MATCH (n)-[:ASSET]->(m:Evidence:Compliance:Asset)
        RETURN
            n.name as dataType,
            n.comment as dataComment,
            m.type as assetType,
            m.serial_no as assetNo,
            m.name as assetName,
            m.usage as assetUsage,
            m.data as assetData,
            m.level as assetLevel,
            m.poc as assetPoC,
            m.user as assetUser,
            m.date as assetDate,
            id(m) as assetId
        """
        assets = self.run_data(database=self.user_db, query=get_asset_cypher)
        
        get_data_list_cypher = f"""
        MATCH (c:Evidence:Compliance:Product{{name:'Asset Manage'}})-[:DATA]->(n:Evidence:Compliance:Data{{name:'{asset_type}', product:'Asset Manage'}})
        return
            n.name as dataType,
            n.comment as dataComment
        """
        data_list = self.run_data(database=self.user_db, query=get_data_list_cypher)
        
        return {'assets': assets, 'data_list': data_list, 'asset_type': asset_type}

    def get_all_asset_list(self):
        search_key = self.request.get('main_search_key', '')
        search_value = self.request.get('main_search_value', '')
        where_cypher = ''
        if search_key and search_value:
            where_cypher = f"WHERE toLower({search_key}) CONTAINS toLower('{search_value}')"
        
        get_all_asset_list_cypher = f"""
        MATCH (c:Evidence:Compliance:Product{{name:'Asset Manage'}})-[:DATA]->(n:Evidence:Compliance:Data)-[:ASSET]->(m:Evidence:Compliance:Asset)
        WITH
            n.name as dataType,
            m.type as assetType,
            m.serial_no as assetNo,
            m.name as assetName,
            m.usage as assetUsage,
            m.data as assetData,
            m.level as assetLevel,
            m.poc as assetPoC,
            m.user as assetUser,
            m.date as assetDate
        ORDER BY
            dataType asc
        {where_cypher}
        RETURN *
        """
        assets = self.run_data(database=self.user_db, query=get_all_asset_list_cypher)
            
        get_data_list_cypher = f"""
            MATCH (c:Evidence:Compliance:Product{{name:'Asset Manage'}})-[:DATA]->(n:Evidence:Compliance:Data)
            where n.name <> 'File'
            with n.name as dataType order by dataType asc
            RETURN
                collect(dataType) as data_list
        """
        result = self.run(database=self.user_db, query=get_data_list_cypher)

        response = {'assets': assets, 'data_list': result['data_list']}

        return response

    def get_file_list(self):
        cypher = f"""
        MATCH (c:Evidence:Compliance:Product{{name:'Asset Manage'}})-[:DATA]->(n:Evidence:Compliance:Data{{name:'File'}})
        OPTIONAL MATCH (n)-[:FILE]->(m:Evidence:Compliance:File)
        RETURN
            m.name as fileName,
            m.comment as fileComment,
            m.author as fileAuthor,
            m.poc as filePoC,
            m.version as fileVersion,
            m.upload_date as uploadDate
        """
        results = self.run_data(database=self.user_db, query=cypher)

        return results


class AssetTableAction(AssetsBase):
    # Asset Table Action
    def asset_table_action(self, action_type):
        if action_type == 'add':
            response = self.add_asset_table()
        elif action_type == 'delete':
            response = self.delete_asset_table()
        elif action_type == 'modify':
            response = self.modify_asset_table()
        return response

    def add_asset_table(self):
        try:
            category_name = self.request.get('category_name', '')
            cypher = f"""
            MATCH (n:Compliance:Evidence:Data{{name:'{category_name}', product:'Asset Manage'}})
            RETURN COUNT(n) AS count
            """
            result = self.run(database=self.user_db, query=cypher)

            if not category_name:
                return 'Please Enter Asset Category Name'
            if 0 < result['count']:
                return "Already Exisiting Asset Category. Please Enter New Asset Category Name."
            
            category_comment = self.request.get('category_comment', '')
            cypher = f"""
            MATCH (c:Evidence:Compliance:Product{{name:'Asset Manage'}})
            MERGE (n:Compliance:Evidence:Data{{name:'{category_name}', comment:'{category_comment}', product:'Asset Manage'}})
            MERGE (c)-[:DATA]->(n)
            """
            self.run(database=self.user_db, query=cypher)  
                          
            return "Successfully Created Asset Category"
        except Exception as e :
            return f'Failed to Create Asset Category. Please Try Again.'

    def delete_asset_table(self):
        category_name = self.request.POST['category_name']
        try:
            cypher = f"""
            MATCH (p:Compliance:Product:Evidence{{name:'Asset Manage'}})-[:DATA]->(n:Compliance:Evidence:Data{{name:'{category_name}', product:'Asset Manage'}})
            OPTIONAL MATCH (n)-[:ASSET]->(a:Compliance:Evidence:Asset)
            DETACH DELETE n, a
            """
            self.run(database=self.user_db, query=cypher)
            return 'Successfully Deleted Asset Category'
        except:
            return 'Failed to Delete Asset Category'

    def modify_asset_table(self):
        try:
            asset_type = self.request.get('asset_type', '')
            category_name = self.request.get('category_name', '')
            cypher = f"""
            MATCH (n:Compliance:Evidence:Data{{name:'{category_name}'}})
            RETURN COUNT(n) AS count
            """
            result = self.run(database=self.user_db, query=cypher)
            
            if not category_name:
                return "Please Enter Asset Category Name"
            if asset_type != category_name and result['count']:
                return "Already Existing Asset Category. Please Enter New Asset Category Name."
            
            category_comment = self.request.get('category_comment', '')
            cypher = f"""
            MATCH (a:Compliance:Evidence:Product{{name:'Asset Manage'}})-[:DATA]->(d:Compliance:Evidence:Data{{name:'{asset_type}', product:'Asset Manage'}})
            SET d.name = '{category_name}', d.comment = '{category_comment}'
            """
            self.run(database=self.user_db, query=cypher)
            
            return "Successfully Modified Asset Category"
        except Exception as e:
            return f"{e}: Failed to Modify Asset Category. Please Try Again."


class AssetFileAction(Neo4jHandler):
    def __init__(self, request) -> None:
        super().__init__()
        self.request = request
        self.request_data = dict(request.POST.items()) if request.method == 'POST' else dict(request.GET.items())
        self.user_db = request.session.get('db_name')
        self.user_uuid = request.session.get('uuid')
        
    # Asset File Action
    def asset_file_action(self, action_type):
        if action_type == 'add':
            return self.add_asset_file()
        elif action_type == 'delete':
            return self.delete_asset_file()
        elif action_type == 'modify':
            return self.modify_asset_file()
        else:
            return 'Fail'

    def add_asset_file(self):
        try:
            # Extract data from the POST request
            uploadedFile = self.request.FILES.get('uploadedFile', '')
            poc = self.request_data.get('poc', '')
            fileComment = self.request_data.get('fileComment', '')
            author = self.request_data.get('author', '')
            version = self.request_data.get('version', '')
            
            cypher = f"""
            MATCH (p:Product:Compliance:Evidence{{name:'Asset Manage'}})-[:DATA]->(a:Compliance:Evidence:Data{{name:'File'}})
            MATCH (a)-[:FILE]->(e:Compliance:Evidence:File{{name:'{uploadedFile.name.replace(' ', '_')}'}})
            RETURN COUNT(e) AS count
            """
            result = self.run(database=self.user_db, query=cypher)
            
            if not uploadedFile:
                return 'Please Select File'
            if 0 < result['count']:
                return "Already Exsisting File. Please Insert Different File."
            if not poc:
                return 'Please Enter Inforamtion for Person of Contact'
            if not fileComment:
                return "Please Enter Comment"
            
            # Saving the information in the database
            # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<< 디비 부분 수정필요
            document = Asset(
                user_uuid = self.user_uuid,
                title=fileComment,
                uploadedFile=uploadedFile
            )
            document.save()
            
            # Add current timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S") # <<<<<<<<<<< 이것도 한국 시간이 아님. 한국 시간으로 수정
            uploadedFile.name = uploadedFile.name.replace(' ', '_')

            # Create or update the node with properties
            add_evidence = f"""
            MATCH (p:Product:Compliance:Evidence{{name:'Asset Manage'}})-[:DATA]->(a:Compliance:Evidence:Data{{name:'File'}})
            MERGE (e:Compliance:Evidence:File{{name:'{uploadedFile.name}', comment:'{fileComment}', upload_date:'{timestamp}', version:'{version}', author:'{author}', poc:'{poc}'}})
            MERGE (a)-[:FILE]->(e)
            RETURN 1 LIMIT 1
            """
            self.run(database=self.user_db, query=add_evidence)
            
            return "Successfully Added Asset File"
        except Exception as e:
            
            return "Failed To Add Asset File. Please Try Again."
        
    def delete_asset_file(self):
        try:
            cypher = f"""
            MATCH (p:Product:Compliance:Evidence{{name:'Asset Manage'}})-[:DATA]->(d:Data:Compliance:Evidence{{name:'File'}})-[:FILE]->(n:Compliance:Evidence:File{{name:'{self.request['file_name']}'}})
            DETACH DELETE n
            RETURN 1 LIMIT 1
            """
            self.run(database=self.user_db, query=cypher)
            documents = Asset.objects.filter(user_uuid=self.user_uuid, title=self.reuqest['file_comment'])
            for document in documents:
                if document.uploadedFile.name.endswith(self.reuqest_data['file_name'].replace('[','').replace(']','')):
                    print(document.uploadedFile.path)
                    document.uploadedFile.delete(save=False)
                    document.delete()
            return "Successfully Deleted Asset File"
        except Exception as e:
            return 'Failed To Delete Asset File. Please Try Again.'

    def modify_asset_file(self):
        try:
            # Extract data from the POST request
            og_fileName = self.request_data.get('og_fileName','')
            file_name = self.request_data.get('fileName','')
            file_comment = self.request_data.get('fileComment','')
            og_comment = self.request_data.get('og_comment', '')
            if not file_name:
                return "Please Check File Name"
            elif not file_comment:
                return "Please Enter File Comment"
            elif og_fileName != file_name:
                raise Exception
            elif not og_comment:
                raise Exception
            else:
                file_author = self.request_data.get('fileAuthor','')
                file_version = self.request_data.get('fileVersion','')
                file_poc = self.request_data.get('filePoC','')

                # Add current timestamp
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Create or update the node with properties
                add_assets = f"""
                MATCH (a:Compliance:Evidence:Product{{name:'Asset Manage'}})-[:DATA]->(d:Compliance:Evidence:Data{{name:'File'}})-[:FILE]->(n:Compliance:Evidence:File{{name:'{file_name}'}})
                SET
                    n.comment = '{file_comment}',
                    n.author = '{file_author}',
                    n.version = '{file_version}',
                    n.poc = '{file_poc}',
                    n.last_update = '{timestamp}'
                RETURN True LIMIT 1
                """
                self.run(database=self.user_db, query=add_assets)
                
                documents = Asset.objects.filter(user_uuid=self.user_uuid, title=og_comment)
                for document in documents:
                    if document.uploadedFile.name.endswith(file_name.replace('[','').replace(']','')):
                        document.title = file_comment
                        document.save()
                        print('modified')
                return "Successfully Modified Asset File"
        except Exception as e:
            print(e)
            return "Failed To Modify Asset File. Please Try Again."


class AssetDataAction(AssetsBase):
    # Asset Data Action
    def asset_data_action(self, action_type):
        if action_type == 'add':
            response = self.add_asset_data()
        elif action_type == 'delete':
            response = self.delete_asset_data()
        elif action_type == 'modify':
            response = self.modify_asset_data()
        else:
            response = 'Fail'
        return response

    def add_asset_data(self):
        try:
            # Extract data from the POST request
            for prop in ['asset_type', 'asset_name', 'serial_number', 'asset_usage', 'asset_data', 'asset_poc']:
                if not self.request[prop]:
                    raise ValueError(prop)
            serial_number = self.request.get('serial_number', '')
            
            get_count_cypher = f"""
            MATCH (n:Compliance:Evidence:Asset {{serial_no: '{serial_number}'}})
            RETURN COUNT(n) AS count
            """
            result = self.run(database=self.user_db, query=get_count_cypher)
            
            if 0 < result['count']:
                return "Already Existing Serial Number. Please Enter New Serial Number."
            else:
                asset_type = self.request['asset_type']
                asset_name = self.request['asset_name']
                asset_usage = self.request['asset_usage']
                asset_data = self.request['asset_data']
                asset_poc = self.request['asset_poc']
                asset_level = self.request['asset_level']
                asset_user = self.request['asset_user']
                asset_category = self.request['asset_category']

                # Add current timestamp
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Create or update the node with properties
                cypher = f"""
                MATCH (a:Compliance:Evidence:Product{{name:'Asset Manage'}})-[:DATA]->(d:Compliance:Evidence:Data{{name:'{asset_category}', product:'Asset Manage'}})
                MERGE (n:Compliance:Evidence:Asset{{
                    type:'{asset_type}',
                    serial_no:'{serial_number}',
                    name:'{asset_name}',
                    usage:'{asset_usage}',
                    data:'{asset_data}',
                    level:'{asset_level}',
                    poc:'{asset_poc}',
                    user:'{asset_user}',
                    date:'{timestamp}'
                    }})
                MERGE (d)-[:ASSET]->(n)
                RETURN 1 LIMIT 1
                """
                self.run(database=self.user_db, query=cypher)

                return "Successfully Added Data"
        except ValueError as e:
            return f"Please Enter {str(e).replace('_', ' ').title()}"
        except Exception as e:
            return f'Error: {str(e)}'

    def delete_asset_data(self, data):
        try:
            serial_number = data.POST.get('serial_number', '')
            if not serial_number:
                raise Exception
            else:
                cypher = f"""
                MATCH (n:Compliance:Evidence:Asset{{serial_no:'{serial_number}'}})
                DETACH DELETE n
                """
                self.run(database=self.user_db, query=cypher)
                return "Successfully Deleted Data"
        except Exception as e:
            return f'Failed To Delete Data. Please Try Again.'

    def modify_asset_data(self):
        try:
            # Extract data from the POST request
            for prop in ['asset_type', 'asset_name', 'serial_number', 'asset_usage', 'asset_data', 'asset_poc']:
                if not self.request[prop]:
                    raise ValueError(prop)
                
            serial_number = self.request.get('serial_number', '')
            asset_id = self.request.get('asset_id', '')
            
            # <<<<<<<<<<<<<<<<<<<<<<<<<<<<< 이부분도 쿼리 두개 나누지말고 하나에서 두 개 결과 뽑게 할 수 있으면 그렇게 하기
            cypher1 = f"""
            MATCH (n:Compliance:Evidence:Asset)
            WHERE ID(n) = {asset_id}
            RETURN n.serial_no AS serial_number
            """
            result1 = self.run(database=self.user_db, query=cypher1)
            
            cypher2 = f"""
            MATCH (n:Compliance:Evidence:Asset {{serial_no:'{serial_number}'}})
            RETURN COUNT(n) AS count
            """
            result2 = self.run(database=self.user_db, query=cypher2)
            
            if result1['serial_number'] != serial_number and 0 < result2['count']:
                return "Already Exsiting Serial Number. Please Enter New Serial Number"
            else:
                asset_type = self.request['asset_type']
                asset_name = self.request['asset_name']
                asset_usage = self.request['asset_usage']
                asset_data = self.request['asset_data']
                asset_poc = self.request['asset_poc']
                asset_level = self.request['asset_level']
                asset_user = self.request['asset_user']
                asset_category = self.request['asset_category']

                # Add current timestamp
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Create or update the node with properties
                cypher = f"""
                MATCH (a:Compliance:Evidence:Product{{name:'Asset Manage'}})-[:DATA]->(d:Compliance:Evidence:Data{{name:'{asset_category}', product:'Asset Manage'}})
                MATCH (d)-[:ASSET]->(n:Compliance:Evidence:Asset)
                WHERE id(n) = {asset_id}
                SET
                    n.type = '{asset_type}',
                    n.serial_no = '{serial_number}',
                    n.name = '{asset_name}',
                    n.usage = '{asset_usage}',
                    n.data = '{asset_data}',
                    n.level = '{asset_level}',
                    n.poc = '{asset_poc}',
                    n.user = '{asset_user}',
                    n.date = '{timestamp}'
                """
                self.run(database=self.user_db, query=cypher)

                return "Successfully Modified Data"
        except ValueError as e:
            return f"Please Enter {str(e).replace('_', ' ').title()}"
        except Exception as e:
            return f'Failed To Modify Data. Please Try Again.'