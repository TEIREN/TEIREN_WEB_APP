from django.contrib.auth.models import User
from django.conf import settings
from py2neo import Graph

# AWS
host = settings.NEO4J['HOST']
port = settings.NEO4J["PORT"]
username = settings.NEO4J['USERNAME']
password = settings.NEO4J['PASSWORD']
graph = Graph(f"bolt://{host}:{port}", auth=(username, password))

def data_masking(text):
    response = ''
    if len(text) > 6:
        masking_text = text[3:-3]
        start = text[:3]
        end = text[-3:]
    else:
        masking_text = text[1:-1]
        start = text[:1]
        end = text[-1:]
    for ch in masking_text:
        if ch in ['-', '@', '.']:
            response += ch
            continue
        response += '*'
    return start+response+end


def get_account_list():
    cypher = f"""
    MATCH (a:Teiren:Account)
    RETURN
        a.userName as userName,
        a.email as email
    ORDER BY id(a) ASC
    """
    response = []
    results = graph.run(cypher)
    for result in results:
        data = dict(result)
        for key, value in data.items():
            if key != "userName":
                data[key] = data_masking(value)
        response.append(data)
    return {'account_list': response}

def verify_account(request):
    userName = request['user_name']
    userPassword = request['user_password']

    cypher = f"""
    MATCH (a:Teiren:Account {{userName:'{userName}'}})
    RETURN
        CASE
            WHEN a.userPassword = '{userPassword}' THEN 'success'
            ELSE 'fail'
        END AS result
    """
    result = graph.run(cypher).data()
    if len(result) < 1:
        response = '[Verification Fail] Unknown Information. Please Try Again.'
    elif result[0]['result'] == 'success':
        cypher = f"""
        MATCH (a:Teiren:Account {{userName:'{userName}'}})
        RETURN
            a.userName as userName,
            a.userPassword as userPassword,
            a.email as email
        """
        results = graph.run(cypher)
        for result in results:
            response = dict(result)
            break
    else:
        response = '[Verification Fail] Wrong Information. Please Try Again.'
    return response

def edit_account(request):
    if request['og_user_name'] != request['user_name']:
        if 0 < graph.evaluate(f"MATCH (a:Teiren:Account {{userName:'{request['user_name']}'}})RETURN COUNT(a)"):
            return f"User Name: {request['user_name']} already exists. Please try different name"
    cypher = f"""
    MATCH (a:Teiren:Account {{userName:'{request['og_user_name']}'}})
    SET
        a.userName = '{request['user_name']}',
        a.userPassword = '{request['user_password']}',
        a.email = '{request['email_add']}'
    RETURN count(a)
    """
    try:
        user = User.objects.get(username=request['og_user_name'])
        user.username = request['user_name']
        user.set_password(request['user_password'])
        user.save()
        if 1 == graph.evaluate(cypher):
            return 'Changed Account Successfully'
        else:
            raise Exception
    except Exception:
        return 'Failed To Edit Account. Please Try Again.'

def delete_account(request):
    for key, value in request.items():
        if not value:
            return f"[{key.replace('_', ' ').title()}] Is Missing. Please Try Again."
    cypher = f"""
    MATCH (a:Teiren:Account {{
            userName:'{request['user_name']}',
            userPassword: '{request['user_password']}'
        }})
    """
    try:
        if 1 != graph.evaluate(f"{cypher} RETURN COUNT(a)"):
            return "Wrong Password. Please Try Again"
        user = User.objects.get(username=request['user_name'])
        user.delete()
        graph.run(f"""{cypher} WITH a
        OPTIONAL MATCH p = (a)-[:DATE|ACTED|CURRENT*]->()
        UNWIND NODES(p) AS node
        DETACH DELETE node
        """)
        if 0 == graph.evaluate(f"{cypher} RETURN COUNT(a)"):
            return "Deleted Account Successfully"
        else:
            raise Exception
    except Exception:
        return "Failed To Delete Account. Please Try Again."
