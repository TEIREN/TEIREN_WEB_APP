from django.conf import settings
from py2neo import Graph
import os
from datetime import datetime
from ..models import Asset

## Graph DB 연동
host = settings.NEO4J['HOST']
port = settings.NEO4J["PORT"]
username = settings.NEO4J['USERNAME']
password = settings.NEO4J['PASSWORD']
graph = Graph(f"bolt://{host}:7688", auth=(username, 'dbdnjs!23'))

# Asset List
def get_asset_list(asset_type):
    results = graph.run(f"""
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
    """)
    assets = []
    for result in results:
        assets.append(dict(result.items()))
        

    results = graph.run(f"""
    MATCH (c:Evidence:Compliance:Product{{name:'Asset Manage'}})-[:DATA]->(n:Evidence:Compliance:Data{{name:'{asset_type}', product:'Asset Manage'}})
    return
        n.name as dataType,
        n.comment as dataComment
    """)
    data_list = []
    for result in results:
        data_list.append(dict(result.items()))

    return {'assets': assets, 'data_list': data_list, 'asset_type': asset_type}


def get_all_asset_list(request):
    print(request.POST.dict())
    search_key = request.POST.get('main_search_key', '')
    search_value = request.POST.get('main_search_value', '')
    where_cypher = ''
    if search_key and search_value:
        where_cypher = f"WHERE toLower({search_key}) CONTAINS toLower('{search_value}')"
    results = graph.run(f"""
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
    """)
    assets = []
    for result in results:
        assets.append(dict(result.items()))


    data_list = graph.evaluate(f"""
        MATCH (c:Evidence:Compliance:Product{{name:'Asset Manage'}})-[:DATA]->(n:Evidence:Compliance:Data)
        where n.name <> 'File'
        with n.name as dataType order by dataType asc
        RETURN
            collect(dataType) as dataType
    """)

    response = {'assets': assets, 'data_list': data_list}

    return response

def get_file_list():
    results = graph.run(f"""
    MATCH (c:Evidence:Compliance:Product{{name:'Asset Manage'}})-[:DATA]->(n:Evidence:Compliance:Data{{name:'File'}})
    OPTIONAL MATCH (n)-[:FILE]->(m:Evidence:Compliance:File)
    RETURN
        m.name as fileName,
        m.comment as fileComment,
        m.author as fileAuthor,
        m.poc as filePoC,
        m.version as fileVersion,
        m.upload_date as uploadDate
    """)
    response = []
    for result in results:
        response.append(dict(result.items()))

    return response

# Asset Table Action
def asset_table_action(request, action_type):
    if action_type == 'add':
        response = add_asset_table(request)
    elif action_type == 'delete':
        response = delete_asset_table(request)
    elif action_type == 'modify':
        response = modify_asset_table(request)
    return response

def add_asset_table(request):
    try:
        category_name = request.POST['category_name']
        if not category_name:
            response = 'Please Enter Asset Category Name'
        elif 0 < graph.evaluate(f"""
            MATCH (n:Compliance:Evidence:Data{{name:'{category_name}', product:'Asset Manage'}})
            RETURN COUNT(n)
            """):
            response = "Already Exisiting Asset Category. Please Enter New Asset Category Name."
        else:
            category_comment = request.POST['category_comment']
            graph.run(f"""
            MATCH (c:Evidence:Compliance:Product{{name:'Asset Manage'}})
            MERGE (n:Compliance:Evidence:Data{{name:'{category_name}', comment:'{category_comment}', product:'Asset Manage'}})
            MERGE (c)-[:DATA]->(n)
            """)
            response = "Successfully Created Asset Category"
    except Exception as e :
        response = f'Failed to Create Asset Category. Please Try Again.'
    finally:
        return response

def delete_asset_table(request):
    category_name = request.POST['category_name']
    try:
        graph.evaluate(f"""
        MATCH (p:Compliance:Product:Evidence{{name:'Asset Manage'}})-[:DATA]->(n:Compliance:Evidence:Data{{name:'{category_name}', product:'Asset Manage'}})
        OPTIONAL MATCH (n)-[:ASSET]->(a:Compliance:Evidence:Asset)
        DETACH DELETE n, a
        """)
        response = "Successfully Deleted Asset Category"
    except:
        response = 'Failed to Delete Asset Category'
    finally:
        return response

def modify_asset_table(request):
    try:
        asset_type = request.POST['asset_type']
        category_name = request.POST['category_name']
        if not category_name:
            response = "Please Enter Asset Category Name"
        elif asset_type != category_name and graph.evaluate(f"""
            MATCH (n:Compliance:Evidence:Data{{name:'{category_name}'}})
            RETURN COUNT(n)
            """):
            response = "Already Existing Asset Category. Please Enter New Asset Category Name."
        else:
            category_comment = request.POST['category_comment']
            graph.run(f"""
            MATCH (a:Compliance:Evidence:Product{{name:'Asset Manage'}})-[:DATA]->(d:Compliance:Evidence:Data{{name:'{asset_type}', product:'Asset Manage'}})
            SET d.name = '{category_name}', d.comment = '{category_comment}'
            """)
            response = "Successfully Modified Asset Category"
    except Exception as e:
        response = f"{e}: Failed to Modify Asset Category. Please Try Again."
    finally:
        return response


# Asset File Action
def asset_file_action(request, action_type):
    if action_type == 'add':
        response = add_asset_file(request)
    elif action_type == 'delete':
        response = delete_asset_file(request)
    elif action_type == 'modify':
        response = modify_asset_file(request)
    else:
        response = 'Fail'
    return response

def add_asset_file(request):
    try:
        # Extract data from the POST request
        uploadedFile = request.FILES.get('uploadedFile', '')
        data = dict(request.POST.items())
        poc = data.get('poc', '')
        fileComment = data.get('fileComment', '')
        if not uploadedFile:
            response = 'Please Select File'
        elif 0 < graph.evaluate(f"""
        MATCH (p:Product:Compliance:Evidence{{name:'Asset Manage'}})-[:DATA]->(a:Compliance:Evidence:Data{{name:'File'}})
        MATCH (a)-[:FILE]->(e:Compliance:Evidence:File{{name:'{uploadedFile.name.replace(' ', '_')}'}})
        RETURN COUNT(e)
        """):
            response = "Already Exsisting File. Please Insert Different File."
        elif not poc:
            response = 'Please Enter Inforamtion for Person of Contact'
        elif not fileComment:
            response = "Please Enter Comment"
        else:
            author = data.get('author', '')
            version = data.get('version', '')
            # Saving the information in the database
            document = Asset(
                title=fileComment,
                uploadedFile=uploadedFile
            )
            document.save()
            # Add current timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            uploadedFile.name = uploadedFile.name.replace(' ', '_')

            # Create or update the node with properties
            add_evidence = f"""
            MATCH (p:Product:Compliance:Evidence{{name:'Asset Manage'}})-[:DATA]->(a:Compliance:Evidence:Data{{name:'File'}})
            MERGE (e:Compliance:Evidence:File{{name:'{uploadedFile.name}', comment:'{fileComment}', upload_date:'{timestamp}', version:'{version}', author:'{author}', poc:'{poc}'}})
            MERGE (a)-[:FILE]->(e)
            """
            graph.run(add_evidence)

            response = "Successfully Added Asset File"
    except Exception as e:
        response = f"Failed To Add Asset File. Please Try Again."
    finally:
        return response

def delete_asset_file(request):
    try:
        data = dict(request.POST.items())
        graph.evaluate(f"""
        MATCH (p:Product:Compliance:Evidence{{name:'Asset Manage'}})-[:DATA]->(d:Data:Compliance:Evidence{{name:'File'}})-[:FILE]->(n:Compliance:Evidence:File{{name:'{data['file_name']}'}})
        DETACH DELETE n
        """)
        documents = Asset.objects.filter(title=data['file_comment'])
        for document in documents:
            if document.uploadedFile.name.endswith(data['file_name'].replace('[','').replace(']','')):
                print(document.uploadedFile.path)
                document.uploadedFile.delete(save=False)
                document.delete()
        response = "Successfully Deleted Asset File"
    except Exception as e:
        print(e)
        response = 'Failed To Delete Asset File. Please Try Again.'
    finally:
        return response

def modify_asset_file(request):
    try:
        # Extract data from the POST request
        data = dict(request.POST.items())
        og_fileName = data.get('og_fileName','')
        file_name = data.get('fileName','')
        file_comment = data.get('fileComment','')
        og_comment = data.get('og_comment', '')
        if not file_name:
            response = "Please Check File Name"
        elif not file_comment:
            response = "Please Enter File Comment"
        elif og_fileName != file_name:
            raise Exception
        elif not og_comment:
            raise Exception
        else:
            file_author = data.get('fileAuthor','')
            file_version = data.get('fileVersion','')
            file_poc = data.get('filePoC','')

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
            """
            graph.evaluate(add_assets)
            documents = Asset.objects.filter(title=og_comment)
            for document in documents:
                if document.uploadedFile.name.endswith(file_name.replace('[','').replace(']','')):
                    document.title = file_comment
                    document.save()
                    print('modified')
            response = "Successfully Modified Asset File"
    except Exception as e:
        print(e)
        response = "Failed To Modify Asset File. Please Try Again."
    finally:
        return response

# Asset Data Action
def asset_data_action(request, action_type):
    if action_type == 'add':
        response = add_asset_data(request)
    elif action_type == 'delete':
        response = delete_asset_data(request)
    elif action_type == 'modify':
        response = modify_asset_data(request)
    else:
        response = 'Fail'
    return response

def add_asset_data(request):
    try:
        # Extract data from the POST request
        data = dict(request.POST.items())
        for prop in ['asset_type', 'asset_name', 'serial_number', 'asset_usage', 'asset_data', 'asset_poc']:
            if not data[prop]:
                raise ValueError(prop)
        serial_number = data.get('serial_number','')
        if 0 < graph.evaluate(f"""
            MATCH (n:Compliance:Evidence:Asset {{serial_no: '{serial_number}'}})
            RETURN COUNT(n)
            """):
            response = "Already Existing Serial Number. Please Enter New Serial Number."
        else:
            asset_type = data.get('asset_type','')
            asset_name = data.get('asset_name','')
            asset_usage = data.get('asset_usage','')
            asset_data = data.get('asset_data','')
            asset_poc = data.get('asset_poc','')
            asset_level = data.get('asset_level','')
            asset_user = data.get('asset_user','')
            asset_category = data.get('asset_category','')

            # Add current timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Create or update the node with properties
            graph.run(f"""
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
            """)

            response = "Successfully Added Data"
    except ValueError as e:
        response = f"Please Enter {str(e).replace('_', ' ').title()}"
    except Exception as e:
        response = f'Error: {str(e)}'
    finally:
        return response

def delete_asset_data(data):
    try:
        serial_number = data.POST.get('serial_number', '')
        if not serial_number:
            raise Exception
        else:
            graph.evaluate(f"""
            MATCH (n:Compliance:Evidence:Asset{{serial_no:'{serial_number}'}})
            DETACH DELETE n
            """)
            response = "Successfully Deleted Data"
    except Exception as e:
        response = f'Failed To Delete Data. Please Try Again.'
    finally:
        return response

def modify_asset_data(request):
    try:
        # Extract data from the POST request
        data = dict(request.POST.items())
        for prop in ['asset_type', 'asset_name', 'serial_number', 'asset_usage', 'asset_data', 'asset_poc']:
            if not data[prop]:
                raise ValueError(prop)
        serial_number = data.get('serial_number','')
        asset_id = data.get('asset_id','')
        if graph.evaluate(f"""
            MATCH (n:Compliance:Evidence:Asset)
            WHERE ID(n) = {asset_id}
            RETURN n.serial_no
            """) != serial_number and 0 < graph.evaluate(f"""
            MATCH (n:Compliance:Evidence:Asset {{serial_no:'{serial_number}'}})
            RETURN COUNT(n)
            """):
                response = "Already Exsiting Serial Number. Please Enter New Serial Number"
        else:
            asset_type = data.get('asset_type','')
            asset_name = data.get('asset_name','')
            asset_usage = data.get('asset_usage','')
            asset_data = data.get('asset_data','')
            asset_poc = data.get('asset_poc','')
            asset_level = data.get('asset_level','')
            asset_user = data.get('asset_user','')
            asset_category = data.get('asset_category','')

            # Add current timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Create or update the node with properties
            graph.run(f"""
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
            """)

            response = "Successfully Modified Data"
    except ValueError as e:
        response = f"Please Enter {str(e).replace('_', ' ').title()}"
    except Exception as e:
        response = f'Failed To Modify Data. Please Try Again.'
    finally:
        return response