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

def get_lists_version(compliance_type, data=None):
    where_version = ''
    where_product = ''
    if data:
        search_key = data['main_search_key']
        search_value = data['main_search_value']
        version = data['version']
        product = data['product']
        if compliance_type == 'Isms_p':
            where_version = f"WHERE i.date = date('{version}')"
            where_product = f"WHERE p.name = '{product}'"
        else:
            where_version = f"WHERE v.date = date('{version}')"
        if search_key and search_value:
            if search_key == 'all':
                where_version += f"""
                    AND ( 
                        toLower(c.name) CONTAINS toLower('{search_value}')
                        OR toLower(c.no) CONTAINS toLower('{search_value}')
                        OR toLower(s.name) CONTAINS toLower('{search_value}')
                        OR toLower(s.no) CONTAINS toLower('{search_value}')
                        OR toLower(a.name) CONTAINS toLower('{search_value}')
                        OR toLower(a.no) CONTAINS toLower('{search_value}')
                        OR toLower(a.comment) CONTAINS toLower('{search_value}')
                    )
                """
            elif search_key == 'comment':
                where_version += f" AND toLower(a.comment) CONTAINS toLower('{search_value}')"
            else:
                where_version += f"""
                    AND (
                        toLower({search_key}.name) CONTAINS toLower('{search_value}')
                        OR toLower({search_key}.no) CONTAINS toLower('{search_value}')
                    )
                """
    else:
        product = 'AWS'

    if compliance_type == 'Isms_p':
        results = graph.run(f"""
        MATCH (i:Compliance:Version{{name:'{compliance_type}'}})-[:CHAPTER]->(c:Chapter:Compliance:Certification)-[:SECTION]->
            (s:Certification:Compliance:Section)-[:ARTICLE]->(a:Certification:Compliance:Article)
        {where_version if where_version else "WHERE i.date = date('2023-10-31')"}
        OPTIONAL MATCH (a)<-[r:COMPLY]-(p:Product:Evidence:Compliance)
        {where_product if where_product else "WHERE p.name = 'AWS'"}
        OPTIONAL MATCH (a)<-[:POLICY]-(d:Data:Evidence:Compliance)<-[:DATA]-(:Policy:Evidence:Compliance)
        OPTIONAL MATCH (a)<-[:EVIDENCE]-(data:Data:Evidence:Compliance)<-[:DATA]-(p)
        WITH split(a.no, '.') as articleNo, c, s, a, coalesce(r, {{score: 0}}) as r, p, i, COLLECT(d)[0] as d,
            COLLECT(data.last_update) + COLLECT(d.last_update) AS last_update
        WITH toInteger(articleNo[0]) AS part1, toInteger(articleNo[1]) AS part2, toInteger(articleNo[2]) AS part3,
            c, s, a, r, p, i, d, last_update
        RETURN
            c.no AS chapterNo,
            c.name AS chapterName,
            s.no AS sectionNo,
            s.name AS sectionName,
            a.no AS articleNo,
            a.name AS articleName,
            a.comment AS articleComment,
            r.score AS complyScore,
            apoc.coll.sort(last_update)[-1] AS lastUpdate,
            i.date AS version,
            d.name AS policy
        ORDER BY part1, part2, part3
        """)
        
    else:
        # 법령은 PRODUCT 가 필요없을 수도 있다? -- 성연과 상의 (법령은 증적을 수집하는게 아니다/product별로 법령은 지키는 것을 보여줄 필요는 없다)
        results = graph.run(f"""
        OPTIONAL MATCH (l:Law{{name:'{compliance_type}'}})-[:VERSION]->(v:Version)-[*]->(a:Article)
        {where_version if where_version else ''}
        WITH l, v, a
        OPTIONAL MATCH (v)-[:CHAPTER]->(c:Chapter)-[:SECTION]->(s:Section)-[:ARTICLE]->(a)
        WITH l, v, c, a, s
        OPTIONAL MATCH (v)-[:CHAPTER]->(c1:Chapter)-[:ARTICLE]->(a)
        WITH
            l, v, c, a, s, c1,
            toInteger(COALESCE(c.no, 0)) + toInteger(COALESCE(c1.no, 0)) as chapterOrder,
            toInteger(a.no) as articleOrder,
            toInteger(s.no) as sectionOrder
        RETURN
            COALESCE(l.name, '') AS lawName,
            COALESCE(COALESCE(c.no + '장', '') + COALESCE(c1.no + '장', ''), '') AS chapterNo,
            COALESCE(COALESCE(c.name, '') + COALESCE(c1.name, ''), '') AS chapterName,
            COALESCE(s.no + '절', '') AS sectionNo,
            COALESCE(s.name, '') AS sectionName,
            COALESCE(a.no + '조', '') AS articleNo,
            COALESCE(a.name, '') AS articleName,
            a.comment AS articleComment
        ORDER BY chapterOrder, sectionOrder, articleOrder
        """)
    response = []
    for result in results:
        response.append(dict(result.items()))
    
    if data:
        return response
    else:
        version_list = graph.evaluate(f"""
            MATCH (n:Compliance:Version{{name:'{compliance_type}'}})       
            return COLLECT(n.date)
        """)

        results = graph.run(f"""
        MATCH (e:Evidence:Compliance{{name:'Evidence'}})-[:PRODUCT]->(p:Evidence:Compliance:Product)
        WHERE NOT p.name ENDS WITH 'Manage'
        RETURN
            p.name as productName
            order by productName
        """)
        resource_list = []
        for result in results:
            resource_list.append(dict(result.items()))
        return {'compliance': response,
                'version_list': version_list,
                'resource_list': resource_list,
                'product': product
                }


def modify_lists_comply(compliance_type, data):
    version = data['version']
    product = data['product']
    article = data['article']
    score = data['value']

    if score  == '0':
        try:
            graph.evaluate(f"""
            MATCH (i:Compliance:Version{{name:'{compliance_type}', date:date('{version}')}})-[:CHAPTER]->(c:Chapter:Compliance:Certification)-[:SECTION]->(n:Certification:Compliance:Section)-[:ARTICLE]->(m:Certification:Compliance:Article{{no:'{article}'}})<-[r:COMPLY]-(p:Product:Evidence:Compliance{{name:'{product}'}})
            detach delete r
            return 0 as score
            """)
            return "Success"
        except:
            return "Fail"
    elif 1 <= int(score) <= 2:
        try:
            if 2 >= graph.evaluate(f"""
            MATCH (i:Compliance:Version{{name:'{compliance_type}', date:date('{version}')}})-[:CHAPTER]->(c:Chapter:Compliance:Certification)-[:SECTION]->(n:Certification:Compliance:Section)-[:ARTICLE]->(m:Certification:Compliance:Article{{no:'{article}'}})
            OPTIONAL MATCH (m)<-[r:COMPLY]-(p:Product:Evidence:Compliance{{name:'{product}'}})
            with i, m, p, r
            call apoc.do.when (r is null,
            'match (pro:Product:Evidence:Compliance{{name:"{product}"}}) merge (m)<-[re:COMPLY{{score:{score}}}]-(pro) return re.score as score',
            'set r.score = {score} return r.score as score',
            {{r:r, p:p, m:m, i:i}})
            yield value
            return value.score as score
            """) >= 1 :
                return "Success"
            else:
                raise Exception
        except Exception:
            return "Fail"
    else:
        return "Fail"
        

def get_lists_details(compliance_type, data):
    print(data)
    results  = graph.run(f"""
    OPTIONAL MATCH (l:Law)-[:VERSION]->(v:Version)-[*]->(a:Article)<-[:MAPPED]->(i:Certification{{no:'{data['no']}'}})<-[*]-
        (i:Compliance:Version{{name:'{compliance_type}', date:date('{data['version']}')}})
    WITH l, v, a, i
    OPTIONAL MATCH (v)-[:CHAPTER]->(c:Chapter)-[:SECTION]->(s:Section)-[:ARTICLE]->(a)<-[:MAPPED]->(i)
    WITH l, v, c, a, i, s
    OPTIONAL MATCH (v)-[:CHAPTER]->(c1:Chapter)-[:ARTICLE]->(a)<-[:MAPPED]->(i)
    RETURN
    COALESCE(l.name, '') AS lawName,
    COALESCE(COALESCE(c.no + '장', '') + COALESCE(c1.no + '장', ''), '') AS chapterNo,
    COALESCE(COALESCE(c.name, '') + COALESCE(c1.name, ''), '') AS chapterName,
    COALESCE(s.no + '절', '') AS sectionNo,
    COALESCE(s.name, '') AS sectionName,
    COALESCE(a.no + '조', '') AS articleNo,
    COALESCE(a.name, '') AS articleName
    ORDER BY lawName
    """)
    law_list = []
    for result in results:
        law_list.append(dict(result.items()))
    
    # query 수정 완
    results = graph.run(f"""
    MATCH (n:Certification:Compliance:Article{{compliance_name:'{compliance_type}', no:'{data['no']}'}})<-[*]-
        (i:Compliance:Version{{name:'{compliance_type}', date:date('{data['version']}')}})
    RETURN
        n.no as articleNo,
        n.name as articleName,
        n.comment as articleComment,
        n.checklist as articleChecklist,
        n.example as articleExample
    """)
    article_list = []
    for result in results:
        article_list.append(dict(result.items()))

    #query 수정 완 
    results = graph.run(f"""
    MATCH (f:File:Compliance:Evidence)<-[:FILE]-(d:Compliance:Evidence:Data)-[:EVIDENCE]->
        (a:Compliance:Certification:Article{{compliance_name:'{compliance_type}', no:'{data['no']}'}})<-[*]-
        (i:Compliance:Version{{name:'{compliance_type}', date:date('{data['version']}')}})
    WITH DISTINCT(d), f
    MATCH (d)<-[:DATA]-(p:Product:Compliance:Evidence{{name:'{data['product']}'}})
    RETURN
        f.name as fileName,
        f.comment as fileComment,
        f.version as fileVersion,
        f.file as dataFile,
        f.last_update as fileLastUpdate,
        f.upload_date as fileUploadDate,
        f.poc as filePoc,
        f.author as fileAuthor,
        d.name as dataName,
        d.comment as dataComment,
        p.name as productName
    """)
    evidence_list = []
    for result in results:
        evidence_list.append(dict(result.items()))

    data_list = graph.evaluate(f"""
    MATCH (p:Product:Evidence:Compliance{{name:'{data['product']}'}})-[:DATA]->(d:Compliance:Evidence:Data)
    WITH d.name as data ORDER BY d.name
    RETURN COLLECT(data)
    """)
    
    policy_list = graph.run(f"""
    MATCH (p:Policy)-[:DATA]->(d:Compliance:Evidence:Data)-[:POLICY]->
        (a:Compliance:Certification:Article{{compliance_name:'{compliance_type}', no:'{data['no']}'}})<-[*]-
        (i:Compliance:Version{{name:'{compliance_type}', date:date('{data['version']}')}})
    WITH DISTINCT(d), p
    RETURN p.name as policy, d as data
    """)

    policy_data_list = graph.evaluate(f"""
    MATCH (p:Policy:Evidence:Compliance)-[:DATA]->(d:Compliance:Evidence:Data)
    WITH DISTINCT(d), p ORDER BY toLower(p.name), toLower(d.name)
    WITH p.name+' > '+d.name AS policy_data
    RETURN COLLECT(policy_data) AS policy_data
    """)

    return {'law_list': law_list,
            'article_list': article_list,
            'evidence_list' : evidence_list,
            'data_list' : data_list,
            'policy_list': policy_list,
            'policy_data_list': policy_data_list,
            'product': data['product'],
            'version': data['version']
    }

def add_compliance_evidence_file(request):
    print(request.POST.dict())
    for key, value in request.POST.dict().items():
        if not value and key not in ['version', 'poc']:
            return f"Please Enter/Select {key.replace('_', ' ').title()}"
    try:
        art_no = request.POST.get('art_no', '')
        compliance = request.POST.get('compliance', '')
        data_name = request.POST.get('data_name', '')
        product = request.POST.get('product', '')
        comment = request.POST.get('comment', '')
        author = request.POST.get('author', '')
        poc = request.POST.get('poc', '')
        version = request.POST.get('version', '')
        com_version = request.POST.get('com_version', '')
        file = request.FILES["file"]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if 0 < graph.evaluate(f"""
        MATCH (p:Product:Evidence:Compliance{{name:'{product}'}})-[*]->(e:Compliance:Evidence:File {{name: '{file.name.replace(' ', '_')}'}})
        RETURN COUNT(e)
        """):
            response = "Already Exsisting File. Please Select New File."
        else:
            graph.evaluate(f"""
            MATCH (a:Compliance:Certification:Article{{compliance_name:'{compliance.replace('-','_').capitalize()}', no:'{art_no}'}})<-[*]-
                (i:Compliance:Version{{name:'{compliance.replace('-','_').capitalize()}', date:date('{com_version}')}})
            MATCH (p:Product:Evidence:Compliance{{name:'{product}'}})-[:DATA]->(n:Compliance:Evidence:Data{{name:'{data_name}'}})
            MERGE (e:Compliance:Evidence:File{{
                    name:'{file.name.replace(' ', '_')}',
                    comment:'{comment}',
                    upload_date:'{timestamp}',
                    last_update:'{timestamp}',
                    version:'{version}',
                    author:'{author}',
                    poc:'{poc}'
                }})
            MERGE (a)<-[:EVIDENCE]-(n)
            MERGE (n)-[:FILE]->(e)
            SET n.last_update = '{timestamp}'
            """)
            # 디비에 파일 정보 저장
            document = Evidence(
                title=comment,
                product=product,
                uploadedFile=file
            )
            document.save()
            response = "Successfully Added Evidence File"
    except Exception as e:
        print(e)
        response = f'Failed To Add Evidence File. Please Try Again.'
    finally:
        return response

def modify_compliance_evidence_file(request):
    for key, value in request.POST.dict().items():
        if not value and key not in ['version', 'author', 'poc']:
            return f"Please Enter/Select {key.replace('_', ' ').title()}"
        elif not value and key in ['art_no', 'og_data_name', 'name', 'og_file_comment']:
            return "Failed To Modify Evidence File. Please Try Again"
    try:
        # Extract data from the POST request
        art_no = request.POST.get('art_no', '')
        compliance = request.POST.get('compliance', '')
        data_name = request.POST.get('data_name', '')
        og_data_name = request.POST.get('og_data_name', '')
        product = request.POST.get('product', '')
        name = request.POST.get('name', '')
        comment = request.POST.get('comment', '')
        og_comment = request.POST.get('og_comment', '')
        author = request.POST.get('author', '')
        poc = request.POST.get('poc', '')
        version = request.POST.get('version', '')
        com_version = request.POST.get('com_version', '')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if data_name != og_data_name:
            cypher = f"""
            MATCH (a:Compliance:Certification:Article{{compliance_name:'{compliance.replace('-','_').capitalize()}', no:'{art_no}'}})<-[*]-
                (i:Compliance:Version{{name:'{compliance.replace('-','_').capitalize()}', date:date('{com_version}')}})
            MATCH (p:Product:Evidence:Compliance{{name:'{product}'}})-[:DATA]->(d:Compliance:Evidence:Data{{name:'{data_name}'}})
            MATCH (od:Compliance:Evidence:Data{{name:'{og_data_name}'}})
            MATCH (a)<-[evidence_rel:EVIDENCE]-(od)-[file_rel:FILE]->(f:Compliance:Evidence:File{{name:'{name}', comment:'{og_comment}'}})
            MERGE (f)<-[:FILE]-(d)-[:EVIDENCE]->(a)
            DELETE evidence_rel
            DELETE file_rel
            SET f.comment = '{comment}',
                f.author = '{author}',
                f.version = '{version}',
                f.poc = '{poc}',
                f.last_update = '{timestamp}',
                od.last_update = '{timestamp}',
                d.last_update = '{timestamp}'
            """
        else:
            # Create or update the node with properties
            cypher = f"""
            MATCH (a:Compliance:Certification:Article{{compliance_name:'{compliance.replace('-','_').capitalize()}', no:'{art_no}'}})<-[*]-
                (i:Compliance:Version{{name:'{compliance.replace('-','_').capitalize()}', date:date('{com_version}')}})
            MATCH (p:Product:Evidence:Compliance{{name:'{product}'}})-[:DATA]->(d:Compliance:Evidence:Data{{name:'{data_name}'}})
            MATCH (a)<-[:EVIDENCE]-(d)-[:FILE]->(f:Compliance:Evidence:File{{name:'{name}', comment:'{og_comment}'}})
            SET f.comment = '{comment}',
                f.author = '{author}',
                f.version = '{version}',
                f.poc = '{poc}',
                f.last_update = '{timestamp}',
                d.last_update = '{timestamp}'
            """
        graph.run(cypher)
        if og_comment != comment:
            documents = Evidence.objects.filter(title=f"{og_comment}")
            for document in documents:
                if document.uploadedFile.name.endswith(name.replace('[','').replace(']','')):
                    document.title = comment
                    document.save()
        response = "Successfully Modified Evidence File"
    except Exception as e:
        print(e)
        response = f'Failed To Modify Evidence File. Please Try Again.'
    finally:
        return response

def delete_compliance_evidence_file(request):
    print(request.POST.dict())
    for key, value in request.POST.dict().items():
        if not value and key not in ['version', 'author', 'poc']:
            return f"Please Enter/Select {key.replace('_', ' ').title()}"
    try:
        art_no = request.POST.get('art_no', '')
        compliance = request.POST.get('compliance', '')
        data_name = request.POST.get('data_name', '')
        product = request.POST.get('product', '')
        name = request.POST.get('name', '')
        comment = request.POST.get('comment', '')
        author = request.POST.get('author', '')
        poc = request.POST.get('poc', '')
        version = request.POST.get('version', '')
        com_version = request.POST.get('com_version', '')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        graph.run(f"""
        MATCH (a:Compliance:Certification:Article{{compliance_name:'{compliance.replace('-','_').capitalize()}', no:'{art_no}'}})<-[*]-
                (i:Compliance:Version{{name:'{compliance.replace('-','_').capitalize()}', date:date('{com_version}')}})
        MATCH (p:Product:Evidence:Compliance{{name:'{product}'}})-[:DATA]->(d:Compliance:Evidence:Data{{name:'{data_name}'}})
        MATCH (a)<-[:EVIDENCE]-(d)-[:FILE]->(f:Compliance:Evidence:File{{name:'{name}', comment:'{comment}', version:'{version}', author:'{author}', poc:'{poc}'}})
        SET d.last_update = '{timestamp}'
        DETACH DELETE f
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
        response = "Failed To Delete Evidence File. Please Try Again."
    finally:
        return response

def add_related_policy(request):
    print(request.POST.dict())
    for key, value in request.POST.dict().items():
        if not value:
            return f"Please Enter/Select Data {key.title()}"
    try:
        policy = request.POST.get('data_name', '').split(' > ')[0]
        data = request.POST.get('data_name', '').split(' > ')[1]
        compliance = request.POST.get('compliance', '').replace('-','_').capitalize()
        com_version = request.POST.get('com_version', '')
        article = request.POST.get('art_no', '')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        graph.evaluate(f"""
        MATCH (a:Compliance:Certification:Article{{compliance_name:'{compliance}', no:'{article}'}})<-[*]-
                (i:Compliance:Version{{name:'{compliance}', date:date('{com_version}')}})
        MATCH (:Policy:Evidence:Compliance {{name:'{policy}'}})-[:DATA]->(d:Data:Evidence:Compliance{{name:'{data}'}})
        MERGE (a)<-[:POLICY]-(d)
        SET d.last_update = '{timestamp}'
        """)
        response = 'Successfully Added Related Policy'
    except Exception as e:
        print(e)
        response = "Failed To Add Related Policy. Please Try Again."
    finally:
        return response

def delete_related_policy(request):
    print(request.POST.dict())
    try:
        policy = request.POST.get('policy', '')
        data = request.POST.get('name', '')
        compliance = request.POST.get('compliance', '').replace('-','_').capitalize()
        com_version = request.POST.get('com_version', '')
        article = request.POST.get('art_no', '')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        graph.evaluate(f"""
        MATCH (a:Compliance:Certification:Article{{compliance_name:'{compliance}', no:'{article}'}})<-[*]-
                (i:Compliance:Version{{name:'{compliance}', date:date('{com_version}')}})
        MATCH (:Policy:Evidence:Compliance {{name:'{policy}'}})-[:DATA]->(d:Data:Evidence:Compliance{{name:'{data}'}})
        MATCH (a)<-[rel:POLICY]-(d)
        SET d.last_update = '{timestamp}'
        DELETE rel
        """)
        response = 'Successfully Deleted Related Policy'
    except Exception as e:
        print(e)
        response = "Failed To Delete Related Policy. Please Try Again."
    finally:
        return response

