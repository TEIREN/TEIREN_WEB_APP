from django.conf import settings
from py2neo import Graph
from datetime import datetime
from ..models import Evidence

## Graph DB 연동
host = settings.NEO4J['HOST']
port = settings.NEO4J["PORT"]
username = settings.NEO4J['USERNAME']
password = settings.NEO4J['PASSWORD']
graph = Graph(f"bolt://{host}:7688", auth=(username, 'dbdnjs!23'))


# data 목록 가져오기
def get_data_list(request, data_name=None):
    try:
        response=[]
        main_search_key = request.POST.get('main_search_key', '')
        main_search_value = request.POST.get('main_search_value', '')
        if data_name:
            results = graph.run(f"""
            MATCH (p:Product:Evidence:Compliance)-[:DATA]->(d:Data:Compliance:Evidence)
            WHERE NOT p.name ENDS WITH "Manage" AND d.name = '{data_name}'
            RETURN d AS data, p AS product
            """)
        elif not main_search_key or not main_search_value:
            results = graph.run(f"""
            MATCH (p:Product:Evidence:Compliance)-[:DATA]->(d:Data:Compliance:Evidence)
            WHERE NOT p.name ENDS WITH "Manage"
            RETURN d AS data, p AS product
            """)
        else:
            results = graph.run(f"""
            MATCH (p:Product:Evidence:Compliance)-[:DATA]->(d:Data:Compliance:Evidence)
            WHERE NOT p.name ENDS WITH "Manage" AND toLower(d.{main_search_key}) CONTAINS toLower('{main_search_value}')
            RETURN d AS data, p AS product
            """)
        for result in results:
            response.append(result)
    except Exception as e:
        print(e)
        response = []
    finally:
        return response

def get_product_list():
    try:
        response = graph.evaluate(f"""
        MATCH (p:Product:Evidence:Compliance)
        WHERE NOT p.name ENDS WITH "Manage"
        WITH p.name as product ORDER BY p.name
        RETURN COLLECT(product)
        """)
    except Exception as e:
        response = []
    finally:
        return response

def get_compliance_list():
    try:
        response = graph.evaluate(f"""
        MATCH (:Compliance)-[:COMPLIANCE]->(c:Compliance)
        WHERE c.name <> 'Evidence'
        WITH replace(toUpper(c.name), '_', '-') as compliance ORDER BY c.name
        RETURN COLLECT(compliance)
        """)
    except Exception as e:
        response = []
    finally:
        return response

def get_compliance_version_list(request):
    try:
        compliance = request.POST.get('compliance', '').replace('-', '_').capitalize()
        response = graph.evaluate(f"""
        MATCH (:Compliance)-[:COMPLIANCE]->(c:Compliance{{name:'{compliance}'}})-[:VERSION]->(v:Version)
        WITH toString(v.date) as version ORDER BY v.date
        RETURN COLLECT(version)
        """)
    except Exception as e:
        response = []
    finally:
        return response

def get_compliance_article_list(request):
    try:
        compliance = request.POST.get('compliance', '').replace('-', '_').capitalize()
        version = request.POST.get('version', '')
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
        results = graph.run(cypher)
        for result in results:
            response.append({'no':result['no'], 'name': result['name']})
        response = sorted(response, key=lambda x: [int(i) for i in x['no'].split('.')])
    except Exception as e:
        print(e)
        response = []
    finally:
        return response

# data 추가
def add_evidence_data(request):
    data = dict(request.POST.items())
    for key, value in data.items():
        if value == '' and key not in ['comment', 'author', ''] :
            return f"Please Enter/Select {key.title()}"
    try:
        last_update = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if 0 < graph.evaluate(f"""
        MATCH (c:Data:Compliance:Evidence{{
            name:'{data['name']}'
        }})
        RETURN count(c)
        """):
            response = "Data Already Exsists. Please Enter Different Name."
        else:
            if data['article'] != '':
                cypher = f"""
                MATCH (e:Compliance:Evidence{{name:'Evidence'}})-[:PRODUCT]->(p:Product:Evidence{{name:'{data['product']}'}})
                MATCH (v:Version{{name:'{data['compliance'].replace('-','_').capitalize()}', date:date('{data['version']}')}})-[*]->(a:Article{{compliance_name:'{data['compliance'].replace('-','_').capitalize()}', no:'{data['article'].split(' ')[0]}'}})
                MERGE (p)-[:DATA]->
                    (d:Data:Compliance:Evidence {{
                    name:'{data['name']}',
                    comment:'{data['comment']}',
                    author:'{data['author']}',
                    last_update:'{last_update}'
                }})-[:EVIDENCE]->(a)
                RETURN COUNT(d)
                """
            elif data['compliance'] != '':
                cypher = f"""
                MATCH (e:Compliance:Evidence{{name:'Evidence'}})-[:PRODUCT]->(p:Product:Evidence{{name:'{data['product']}'}})
                MATCH (c:Version:Compliance{{name:'{data['compliance'].replace('-','_').capitalize()}', date:date('{data['version']}')}})
                MERGE (p)-[:DATA]->
                    (d:Data:Compliance:Evidence {{
                    name:'{data['name']}',
                    comment:'{data['comment']}',
                    author:'{data['author']}',
                    last_update:'{last_update}'
                }})-[:EVIDENCE]->(c)
                RETURN COUNT(d)
                """
            else:
                raise Exception
            if 0 == graph.run(cypher):
                raise Exception
            else:
                response = "Successfully Create Data."
    except Exception as e:
        print(e)
        response = "Failed To Create Data. Please Try Again."
    finally:
        return response

def modify_evidence_data(request):
    try:
        og_name=request.POST.get('og_name', '')
        name = request.POST.get('name', '')
        if not name:
            response = "Please Enter Data Name"
        elif not og_name:
            raise Exception
        elif og_name != name and 0 < graph.evaluate(f"""
        MATCH (c:Data:Compliance:Evidence{{
            name:'{name}'
        }})
        RETURN count(c)
        """):
            response = "Data Name Already Exsists. Please Enter New Data Name."
        else:
            comment = request.POST.get('comment', '')
            author = request.POST.get('author', '')
            last_update = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            graph.evaluate(f"""
                MATCH (d:Data:Compliance{{name:'{og_name}'}})
                SET d.name = '{name}',
                    d.comment='{comment}',
                    d.author='{author}',
                    d.last_update='{last_update}' 
                RETURN COUNT(d)
            """)
            response = "Successfully Modified Data"
    except Exception as e:
        print(e)
        response = 'Failed To Modify Data. Please Try Again.'
    finally:
        return response

def delete_evidence_data(request):
    try:
        name = request.POST.get('name', '')
        comment = request.POST.get('comment', '')
        author = request.POST.get('author', '')
        if not name:
            raise Exception
        elif 0 < graph.evaluate(f"""
        MATCH (d:Compliance:Evidence:Data{{name:'{name}', comment:'{comment}', author:'{author}'}})
        OPTIONAL MATCH (d)-[:FILE]->(f:File:Compliance:Evidence)
        RETURN COUNT(f)
        """):
            response = f"There Are Files In [ {name} ] Data. Please Try After Deleting The Files."
        else:
            graph.evaluate(f"""
            MATCH (d:Compliance:Evidence:Data{{name:'{name}', comment:'{comment}', author:'{author}'}})
            DETACH DELETE d
            """)
            response = "Successfully Deleted Data"
    except Exception as e:
        print(e)
        response = "Failed To Delete Data. Please Try Again."
    finally:
        return response


def get_file_list(data_name):
    try:
        response = graph.evaluate(f"""
            MATCH (d:Data:Compliance:Evidence{{name:'{data_name}'}})-[:FILE]->(file:File:Compliance:Evidence)
            RETURN collect(file)
        """)
    except Exception as e:
        print(e)
        response = []
    finally:
        return response

def get_data_related_compliance(search_cate=None, search_content=None):
    try:
        response=[]
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
        results = graph.run(cypher)
        for result in results:
            response.append(result)
    except Exception as e:
        print(e)
        response = []
    finally:
        return response

def add_evidence_file(request):
    for key, value in request.POST.dict().items():
            if not value:
                return f"Please Enter/Select {key.capitalize()}"
    try:
        print(request.POST.dict())
        data_name = request.POST.get('data_name','')
        uploaded_file = request.FILES.get("file")
        product = request.POST.get('product', '')
        if 0 < graph.evaluate(f"""
        MATCH (p:Product:Evidence:Compliance{{name:'{product}'}})-[*]->(f:File:Evidence:Compliance{{name:'{uploaded_file.name}'}})
        RETURN count(f)
        """):
            response = "File Name Already Exsists. Please Enter New File Name."
        else:
            comment = request.POST.get('comment','')
            author = request.POST.get('author','')
            version = request.POST.get('version','')
            poc = request.POST.get('poc','')
            upload_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            graph.evaluate(f"""
            MATCH (d:Data:Compliance:Evidence{{name:'{data_name}'}})
            MERGE (f:File:Compliance:Evidence {{
                name:'{uploaded_file.name.replace(' ', '_')}',
                comment:'{comment}',
                author:'{author}',
                poc:'{poc}',
                version:'{version}',
                upload_date:'{upload_date}'
            }})
            MERGE (d)-[:FILE]->(f)
            SET d.last_update='{upload_date}'
            """)

            # Saving the information in the database
            document = Evidence(
                title= comment,
                product= product,
                uploadedFile=uploaded_file
            )
            document.save()
            response = "Successfully Added Evidence File"
    except Exception as e:
        print(e)
        response = 'Failed To Add Evidence File. Please Try Again.'
    finally:
        return response

def modify_evidence_file(request):
    for key, value in request.POST.dict().items():
        if not value:
            return f"Please Enter/Select {key.capitalize()}"
    try:
        data_name = request.POST.get('data_name', '')
        name = request.POST.get('name', '')
        comment = request.POST.get('comment', '')
        og_comment = request.POST.get('og_comment', '')
        author = request.POST.get('author', '')
        version = request.POST.get('version', '')
        poc = request.POST.get('poc', '')
        last_update = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        graph.evaluate(f"""
        MATCH (d:Data:Compliance{{name:'{data_name}'}})-[:FILE]->(f:File:Evidence:Compliance{{name:'{name}'}})
        SET f.comment='{comment}', 
            f.author='{author}', 
            f.version='{version}',
            f.poc='{poc}',
            f.last_update='{last_update}',
            d.last_update='{last_update}'
        """)

        if og_comment != comment:
            documents = Evidence.objects.filter(title=f"{og_comment}")
            for document in documents:
                if document.uploadedFile.name.endswith(name.replace('[','').replace(']','')):
                    document.title = comment
                    document.save()

        response = "Successfully Modified Evidence File"
    except Exception as e:
        print(e)
        response = "Failed To Modify Evidence File"
    finally:
        return response

def delete_evidence_file(request):
    try:
        data_name = request.POST.get('data_name', '')
        name = request.POST.get('name', '')
        comment = request.POST.get('comment', '')
        author = request.POST.get('author', '')
        version = request.POST.get('version', '')
        poc = request.POST.get('poc', '')
        upload_date = request.POST.get('upload_date', '')
        last_update = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        graph.evaluate(f"""
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
        """)
        documents = Evidence.objects.filter(title=comment)
        for document in documents:
            if document.uploadedFile.name.endswith(name.replace('[','').replace(']','')):
                print(document.uploadedFile.path)
                document.uploadedFile.delete(save=False)
                document.delete()
        response = "Successfully Deleted Evidence File"
    except Exception as e:
        print(e)
        response = "Failed To Delete Evidence File"
    finally:
        return response

def add_related_compliance(request):
    try:
        print(request.POST.dict())
        data_name = request.POST.get('data_name', '')
        compliance = request.POST.get('compliance', '')
        version = request.POST.get('version', '')
        article = request.POST.get('article', '')        
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
        print(cypher)
        graph.evaluate(cypher)
        response = "Successfully Added Related Complicance"
    except Exception as e:
        print(e)
        response = "Failed To Add Related Complicance. Please Try Again."
    finally:
        return response

def delete_related_compliance(request):
    try:
        print(request.POST.dict())
        data_name = request.POST.get('data_name', '')
        compliance = request.POST.get('compliance', '')
        version = request.POST.get('version', '')
        article = request.POST.get('article', '')        
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
        print(cypher)
        graph.evaluate(cypher)
        response = "Successfully Deleted Related Complicance"
    except Exception as e:
        print(e)
        response = "Failed To Delete Related Complicance. Please Try Again."
    finally:
        return response