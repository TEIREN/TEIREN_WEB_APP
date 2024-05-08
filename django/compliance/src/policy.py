from django.conf import settings
from py2neo import Graph
from datetime import datetime
from ..models import Policy

## Graph DB 연동
host = settings.NEO4J['HOST']
port = settings.NEO4J["PORT"]
username = settings.NEO4J['USERNAME']
password = settings.NEO4J['PASSWORD']
graph = Graph(f"bolt://{host}:7688", auth=(username, 'dbdnjs!23'))


def get_policy_data_list(request):
    try:
        response=[]
        main_search_key = request.POST.get('main_search_key', '')
        main_search_value = request.POST.get('main_search_value', '')

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
        results = graph.run(cypher)
        print(cypher)
        for result in results:
            response.append(result)
    except Exception as e:
        print(e)
        response = []
    finally:
        return response

def add_policy(request):
    try:
        policy = request.POST.get('policy','')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not policy:
            response = "Please Enter Policy Name"
        elif 0 < graph.evaluate(f"""
        MATCH (:Evidence:Compliance)-[:PRODUCT]->(:Product{{name:'Policy Manage'}})-[:POLICY]->(p:Policy {{name:'{policy}'}})
        RETURN COUNT(p)
        """):
            response = "Policy Already Exists. Please Enter New Policy Name"
        else:
            graph.run(f"""
            MATCH (:Evidence:Compliance)-[:PRODUCT]->(product:Product{{name:'Policy Manage'}})
            MERGE (p:Policy:Evidence:Compliance {{name:'{policy}', last_update:'{timestamp}'}})
            MERGE (product)-[:POLICY]->(p)
            """)
            response = "Successfully Created Policy"
    except Exception as e:
        print(e)
        response = "Failed To Create Policy. Please Try Again."
    finally:
        return response

def modify_policy(request):
    try:
        og_policy = request.POST.get('og_policy', '')
        policy = request.POST.get('policy', '')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not og_policy:
            raise Exception
        elif not policy:
            response = "Please Enter Policy Name"
        elif 0 < graph.evaluate(f"""
        MATCH (:Evidence:Compliance)-[:PRODUCT]->(:Product{{name:'Policy Manage'}})-[:POLICY]->(p:Policy {{name:'{policy}'}})
        RETURN COUNT(p)
        """):
            response = "Policy Already Exists. Please Enter New Policy Name"
        else:
            graph.evaluate(f"""
            MATCH (:Product{{name:'Policy Manage'}})-[:POLICY]->(p:Policy {{name:'{og_policy}'}})
            SET p.name = '{policy}',
                p.last_update = '{timestamp}'
            """)
            response = "Successfully Modified Policy"
    except Exception as e:
        print(e)
        response ="Failed To Modify Policy. Please Try Again."
    finally:
        return response

def delete_policy(request):
    try:
        policy = request.POST.get('policy', '')
        if not policy:
            raise Exception
        else:
            graph.evaluate(f"""
            MATCH (:Product{{name:'Policy Manage'}})-[:POLICY]->(p:Policy {{name:'{policy}'}})
            OPTIONAL MATCH (p)-[:DATA]->(d:Data:Evidence:Compliance)
            OPTIONAL MATCH (d)-[:FILE]->(f:File:Evicence:Compliance)
            DETACH DELETE p
            DETACH DELETE d
            DETACH DELETE f
            """)
            response = 'Successfully Deleted Policy'
    except Exception as e:
        print(e)
        response = 'Failed To Delete Policy. Please Try Again.'
    finally:
        return response

def add_policy_data(request):
    for key, value in request.POST.dict().items():
        if not value:
            return f"Please Enter/Select Data {key.title()}"
    try:
        policy = request.POST.get('policy', '')
        name = request.POST.get('name', '')
        comment = request.POST.get('comment', '')
        author = request.POST.get('author', '')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if 0 < graph.evaluate(f"""
        MATCH (:Product{{name:'Policy Manage'}})-[:POLICY]->(p:Policy {{name:'{policy}'}})-[:DATA]->(d:Data {{name:'{name}'}})
        RETURN COUNT(d)
        """):
            response = "Policy Data Name Already Exists. Please Enter New Policy Data Name."
        else:
            graph.evaluate(f"""
            MATCH (:Product{{name:'Policy Manage'}})-[:POLICY]->(p:Policy {{name:'{policy}'}})
            MERGE (d:Data:Evidence:Compliance {{name:'{name}', comment:'{comment}', author:'{author}', last_update:'{timestamp}'}})
            MERGE (p)-[:DATA]->(d)
            """)
            response = "Successfully Added Policy Data"
    except Exception as e:
        print(e)
        response ="Failed To Add Policy Data. Please Try Again."
    finally:
        return response

def modify_policy_data(request):
    for key, value in request.POST.dict().items():
        if not value and key not in ['og_name']:
            return f"Please Enter/Select Data {key.title()}"
    try:
        policy = request.POST.get('policy', '')
        name = request.POST.get('name', '')
        og_name = request.POST.get('og_name', '')
        comment = request.POST.get('comment', '')
        author = request.POST.get('author', '')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if og_name != name and 0 < graph.evaluate(f"""
        MATCH (:Product{{name:'Policy Manage'}})-[:POLICY]->(p:Policy {{name:'{policy}'}})-[:DATA]->(d:Data {{name:'{name}'}})
        RETURN COUNT(d)
        """):
            response = "Policy Data Name Already Exists. Please Enter New Policy Data Name."
        else:
            graph.evaluate(f"""
            MATCH (:Product{{name:'Policy Manage'}})-[:POLICY]->(p:Policy {{name:'{policy}'}})-[:DATA]->(d:Data {{name:'{og_name}'}})
            SET d.name = '{name}',
                d.comment = '{comment}',
                d.author = '{author}',
                d.last_update = '{timestamp}'
            """)
            response = "Successfully Modified Policy Data"
    except Exception as e:
        print(e)
        response ="Failed To Modify Policy Data. Please Try Again."
    finally:
        return response

def delete_policy_data(request):
    # for key, value in request.POST.dict().items():
    #     if not value:
    #         return f"Please Enter/Select Data {key.title()}"
    try:
        policy = request.POST.get('policy', '')
        name = request.POST.get('name', '')
        comment = request.POST.get('comment', '')
        author = request.POST.get('author', '')
        cypher = f"""
        MATCH (:Product{{name:'Policy Manage'}})-[:POLICY]->(p:Policy {{name:'{policy}'}})
        MATCH (p)-[:DATA]->(d:Data {{
                name:'{name}',
                comment:'{comment}',
                author:'{author}'
            }})
        OPTIONAL MATCH (d)-[:FILES]->(f)
        """
        if 0 < graph.evaluate(f"{cypher} RETURN COUNT(f)"):
            data_file_list = []
            print(graph.evaluate(f"{cypher} RETURN COUNT(f)"))
            results = graph.run(f"{cypher} RETURN {{name: f.name, comment: f.commnet}} AS file")
            for result in results:
                data_file_list.append(result)
            print(data_file_list)
            response = "test"
        
        if 0 < graph.evaluate(f"{cypher} RETURN COUNT(d)"):
            graph.run(f"{cypher} DETACH DELETE d")
            response = "Successfully Deleted Policy Data"
        else:
            raise Exception

    except Exception as e:
        print(e)
        response ="Failed To Delete Policy Data. Please Try Again."
    finally:
        return response

def get_policy_data_details(policy_type, data_type):
    try:
        if not policy_type or not data_type:
            raise Exception
        else:
            data = graph.evaluate(f"""
            MATCH (:Evidence:Compliance)-[:PRODUCT]->(:Product{{name:'Policy Manage'}})-[:POLICY]->(policy:Policy{{name:'{policy_type}'}})-[:DATA]->(data:Data:Evidence{{name:'{data_type}'}})
            RETURN data
            """)
            
            file_list = graph.evaluate(f"""
            MATCH (:Evidence:Compliance)-[:PRODUCT]->(:Product{{name:'Policy Manage'}})-[:POLICY]->(policy:Policy{{name:'{policy_type}'}})-[:DATA]->(data:Data:Evidence{{name:'{data_type}'}})
            MATCH (data)-[:FILE]->(file)
            RETURN COLLECT(file)
            """)

            response = {'data': data, 'file_list': file_list}
    except Exception as e:
        print(e)
        response = {'data':{}, 'file_list':[]}
    finally:
        return response


def add_policy_data_file(request):
    for key, value in request.POST.dict().items():
        if not value:
            return f"Please Enter/Select Data {key.title()}"
    try:
        file = request.FILES.get('file', '')
        file_name = file.name.replace(' ', '_')
        if 0 < graph.evaluate(f"""
        MATCH (f:File:Compliance:Evidence {{name:'{file_name}'}})
        RETURN COUNT(f)
        """):
            response = "Data File Already Exsists. Please Select New File"
        else:
            policy = request.POST.get('policy', '')
            name = request.POST.get('name', '')
            comment = request.POST.get('comment', '')
            author = request.POST.get('author', '')
            version = request.POST.get('version', '')
            poc = request.POST.get('poc', '')
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            graph.evaluate(f"""
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
            """)
            # 디비에 파일 정보 저장
            document = Policy(
                title=comment,
                uploadedFile=file
            )
            document.save()
            response = "Successfully Added Policy Data File"
    except Exception as e:
        print(e)
        response ="Failed To Add Policy Data File. Please Try Again."
    finally:
        return response

def modify_policy_data_file(request):
    print(request.POST.dict())
    for key, value in request.POST.dict().items():
        if not value:
            return f"Please Enter/Select {key.capitalize()}"
    try:
        policy = request.POST.get('policy', '')
        data_name = request.POST.get('name', '')
        file_name = request.POST.get('file', '')
        comment = request.POST.get('comment', '')
        og_comment = request.POST.get('og_comment', '')
        author = request.POST.get('author', '')
        version = request.POST.get('version', '')
        poc = request.POST.get('poc', '')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cypher = f"""
        MATCH (:Evidence:Compliance)-[:PRODUCT]->(:Product{{name:'Policy Manage'}})-[:POLICY]->(p:Policy{{name:'{policy}'}})-[:DATA]->(d:Data:Evidence{{name:'{data_name}'}})
        MATCH (d)-[:FILE]->(f:File:Evidence:Compliance{{name:'{file_name}'}})
        """
        if 0 < graph.evaluate(f"{cypher} RETURN COUNT(f)"):
            graph.evaluate(f"""
            {cypher}
            SET f.comment = '{comment}', 
                f.author = '{author}', 
                f.version = '{version}',
                f.poc = '{poc}',
                f.last_update = '{timestamp}',
                d.last_update = '{timestamp}'
            """)
            if og_comment != comment:
                documents = Policy.objects.filter(title=f"{og_comment}")
                for document in documents:
                    if document.uploadedFile.name.endswith(file_name.replace('[','').replace(']','')):
                        document.title = comment
                        document.save()
                        print('modified')
        else:
            raise Exception
        response = "Successfully Modified Policy Data File"
    except Exception as e:
        print(e)
        response ="Failed To Modify Policy Data File. Please Try Again."
    finally:
        return response

def delete_policy_data_file(request):
    print(request.POST.dict())
    try:
        policy = request.POST.get('policy', '')
        data_name = request.POST.get('name', '')
        file_name = request.POST.get('file', '')
        comment = request.POST.get('comment', '')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cypher = f"""
        MATCH (:Evidence:Compliance)-[:PRODUCT]->(:Product{{name:'Policy Manage'}})-[:POLICY]->(p:Policy{{name:'{policy}'}})-[:DATA]->(d:Data:Evidence{{name:'{data_name}'}})
        MATCH (d)-[:FILE]->(f:File:Evidence:Compliance{{
            name:'{file_name}',
            comment:'{comment}'
        }})
        """
        if 0 < graph.evaluate(f"{cypher} RETURN COUNT(f)"):
            graph.evaluate(f"{cypher} DETACH DELETE f SET d.last_update = '{timestamp}'")
            documents = Policy.objects.filter(title=comment)
            for document in documents:
                if document.uploadedFile.name.endswith(file_name.replace('[','').replace(']','')):
                    print(document.uploadedFile.path)
                    document.uploadedFile.delete(save=False)
                    document.delete()
        else:
            raise Exception
        response = "Successfully Deleted Policy Data File"
    except Exception as e:
        print(e)
        response ="Failed To Delete Policy Data File. Please Try Again."
    finally:
        return response
