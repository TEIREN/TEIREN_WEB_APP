# # local
# import requests
# from datetime import datetime, date
# from common.neo4j.handler import Neo4jHandler

# # django
# from django.conf import settings
# from django.contrib.auth.signals import user_logged_out
# from django.contrib.auth import get_user_model
# from django.dispatch import receiver

# # 3rd party
# from neo4j import GraphDatabase

# # AWS
# HOST = settings.NEO4J['HOST']
# PORT = settings.NEO4J["PORT"]
# USER = settings.NEO4J['USERNAME']
# PW = settings.NEO4J['PASSWORD']

# URI = f"bolt://{settings.NEO4J['HOST']}:{settings.NEO4J['PORT']}"


# class AuthTrigger(Neo4jHandler):
#     def __init__(self) -> None:
#         super().__init__()

# def login_success(userName, srcip, db_name):
#     print('testsetset')
#     dstip = get_server_ip()
#     print(dstip)
#     query = f"""
#     MATCH (a:Account:Teiren{{
#         userName: '{userName}'
#     }})
#     SET a.failCount = 0
#     WITH a
#     OPTIONAL MATCH (a)-[:DATE]-(d:Date {{date:'{str(date.today())}'}})
#     WITH a, d
#     CALL apoc.do.when(
#         d IS NULL,
#         "MERGE (a)-[:DATE]->(d:Date {{date:'{str(date.today())}'}}) RETURN d",
#         "MATCH (a)-[:DATE]->(d:Date {{date:'{str(date.today())}'}}) RETURN d",
#         {{a:a}}
#     ) YIELD value
#     WITH a, value.d as d
#     OPTIONAL MATCH (a)-[c:CURRENT]->(b:Log:Teiren)
#     WHERE split(b.eventTime,'T')[0] = d.date
#     WITH a, b, d
#     OPTIONAL MATCH (a)-[c:CURRENT]->()
#     DELETE c
#     WITH a, b, d
#     CALL apoc.do.when(
#         b IS NULL,
#         "
#             MERGE (a)-[:CURRENT]->(l:Log:Teiren{{userName: a.userName, eventName:'Login', eventResult: 'Success', eventTime:'{str(datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))}', sourceIp:'{srcip}', serverIp: '{dstip}'}})
#             MERGE (d)-[:ACTED]->(l)
#             RETURN a
#         ",
#         "
#             MERGE (a)-[:CURRENT]->(l:Log:Teiren{{userName: a.userName, eventName:'Login', eventResult: 'Success', eventTime:'{str(datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))}', sourceIp:'{srcip}', serverIp: '{dstip}'}})<-[:ACTED]-(b)
#             RETURN a
#         ",
#         {{a:a, b:b, d:d}}
#     ) YIELD value
#     RETURN value.a.failCount
#     """
#     with GraphDatabase.driver(URI, auth=(USER, PW)) as driver:
#         with driver.session(database=db_name) as session:
#             session.run(query)
            
#     return 0

# def login_fail(userName, srcip):
#     user = get_user_model().objects.get(username=userName)
#     db_name = user.db_name
#     dstip = get_server_ip()
    
#     query = f"""
#     MATCH (a:Account:Teiren{{
#         userName: '{userName}'
#     }})
#     SET a.failCount = a.failCount + 1
#     WITH a
#     OPTIONAL MATCH (a)-[:DATE]-(d:Date {{date:'{str(date.today())}'}})
#     WITH a, d
#     CALL apoc.do.when(
#         d IS NULL,
#         "MERGE (a)-[:DATE]->(d:Date {{date:'{str(date.today())}'}}) RETURN d",
#         "MATCH (a)-[:DATE]->(d:Date {{date:'{str(date.today())}'}}) RETURN d",
#         {{a:a}}
#     ) YIELD value
#     WITH a, value.d as d
#     OPTIONAL MATCH (a)-[c:CURRENT]->(b:Log:Teiren)
#     WHERE split(b.eventTime,'T')[0] = d.date
#     WITH a, b, d
#     OPTIONAL MATCH (a)-[c:CURRENT]->()
#     DELETE c
#     WITH a, b, d
#     CALL apoc.do.when(
#         b IS NULL,
#         "
#             MERGE (a)-[:CURRENT]->(l:Log:Teiren{{userName: a.userName, eventName:'Login', eventResult: 'Fail', eventTime:'{str(datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))}', sourceIp:'{srcip}', serverIp: '{dstip}'}})
#             MERGE (d)-[:ACTED]->(l)
#             RETURN a
#         ",
#         "
#             MERGE (a)-[:CURRENT]->(l:Log:Teiren{{userName: a.userName, eventName:'Login', eventResult: 'Fail', eventTime:'{str(datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))}', sourceIp:'{srcip}', serverIp: '{dstip}'}})<-[:ACTED]-(b)
#             RETURN a
#         ",
#         {{a:a, b:b, d:d}}
#     ) YIELD value
#     RETURN value.a.failCount
#     """
#     with GraphDatabase.driver(URI, auth=(USER, PW)) as driver:
#         with driver.session(database=db_name) as session:
#             failCount = session.run(query)
            
#     return failCount

# @receiver(user_logged_out)
# def logout_success(sender, request, **kwargs):
#     db_name = request.session.get('db_name')
#     with GraphDatabase.driver(URI, auth=(USER, PW)) as driver:
#         with driver.session(database=db_name) as session:
#             srcip = get_client_ip(request)
#             dstip = get_server_ip()
            
#             query = f"""
#             MATCH (a:Account:Teiren{{
#                 userName: '{request.user}'
#             }})
#             WITH a
#             OPTIONAL MATCH (a)-[:DATE]-(d:Date {{date:'{str(date.today())}'}})
#             WITH a, d
#             CALL apoc.do.when(
#                 d IS NULL,
#                 "MERGE (a)-[:DATE]->(d:Date {{date:'{str(date.today())}'}}) RETURN d",
#                 "MATCH (a)-[:DATE]->(d:Date {{date:'{str(date.today())}'}}) RETURN d",
#                 {{a:a}}
#             ) YIELD value
#             WITH a, value.d as d
#             OPTIONAL MATCH (a)-[c:CURRENT]->(b:Log:Teiren)
#             WHERE split(b.eventTime,'T')[0] = d.date
#             WITH a, b, d
#             OPTIONAL MATCH (a)-[c:CURRENT]->()
#             DELETE c
#             WITH a, b, d
#             CALL apoc.do.when(
#                 b IS NULL,
#                 "
#                     MERGE (a)-[:CURRENT]->(l:Log:Teiren{{userName: a.userName, eventName:'Logout', eventResult: 'Success', eventTime:'{str(datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))}', sourceIp:'{srcip}', serverIp: '{dstip}'}})
#                     MERGE (d)-[:ACTED]->(l)
#                     RETURN a",
#                 "
#                     MERGE (a)-[:CURRENT]->(l:Log:Teiren{{userName: a.userName, eventName:'Logout', eventResult: 'Success', eventTime:'{str(datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))}', sourceIp:'{srcip}', serverIp: '{dstip}'}})<-[:ACTED]-(b)
#                     RETURN a
#                 ",
#                 {{a:a, b:b, d:d}}
#             ) YIELD value
#             RETURN value
#             """
#             session.run(query)
#             return 0

# def get_client_ip(request):
#     x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
#     if x_forwarded_for:
#         ip = x_forwarded_for.split(',')[0]
#     else:
#         ip = request.META.get('REMOTE_ADDR')
#     return ip

# def get_server_ip():
#     try:
#         dstip = requests.get('http://169.254.169.254/latest/meta-data/public-ipv4', timeout=2).text
#     except requests.exceptions.RequestException:
#         dstip = '127.0.0.1'
#     print(dstip)
#     return dstip


import logging
import requests
from datetime import datetime, date
from django.conf import settings
from django.contrib.auth.signals import user_logged_out
from django.contrib.auth import get_user_model
from django.dispatch import receiver
from neo4j import GraphDatabase

# 설정 로드
HOST = settings.NEO4J['HOST']
PORT = settings.NEO4J["PORT"]
USER = settings.NEO4J['USERNAME']
PW = settings.NEO4J['PASSWORD']
URI = f"bolt://{settings.NEO4J['HOST']}:{settings.NEO4J['PORT']}"

# 로깅 설정
logger = logging.getLogger(__name__)

class AuthTrigger:
    def __init__(self):
        self.driver = GraphDatabase.driver(URI, auth=(USER, PW))

    def close(self):
        self.driver.close()

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_server_ip():
    try:
        response = requests.get('http://169.254.169.254/latest/meta-data/public-ipv4', timeout=2)
        response.raise_for_status()  # HTTPError 발생시 예외 처리
        dstip = response.text.strip()
    except requests.exceptions.RequestException as e:
        logger.error(f'Failed to get server IP: {e}')
        dstip = '127.0.0.1'
    except Exception as e:
        logger.error(f'Unexpected error: {e}')
        dstip = '127.0.0.1'

    logger.debug(f'Server IP: {dstip}')
    return dstip

def login_success(userName, srcip, db_name):
    logger.debug('login_success function called')
    dstip = get_server_ip()
    logger.debug(f'Destination IP: {dstip}')
    
    query = f"""
    MATCH (a:Account:Teiren {{
        userName: '{userName}'
    }})
    SET a.failCount = 0
    WITH a
    OPTIONAL MATCH (a)-[:DATE]-(d:Date {{date:'{str(date.today())}'}})
    WITH a, d
    CALL apoc.do.when(
        d IS NULL,
        "MERGE (a)-[:DATE]->(d:Date {{date:'{str(date.today())}'}}) RETURN d",
        "MATCH (a)-[:DATE]->(d:Date {{date:'{str(date.today())}'}}) RETURN d",
        {{a:a}}
    ) YIELD value
    WITH a, value.d as d
    OPTIONAL MATCH (a)-[c:CURRENT]->(b:Log:Teiren)
    WHERE split(b.eventTime,'T')[0] = d.date
    WITH a, b, d
    OPTIONAL MATCH (a)-[c:CURRENT]->()
    DELETE c
    WITH a, b, d
    CALL apoc.do.when(
        b IS NULL,
        "
            MERGE (a)-[:CURRENT]->(l:Log:Teiren{{userName: a.userName, eventName:'Login', eventResult: 'Success', eventTime:'{str(datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))}', sourceIp:'{srcip}', serverIp: '{dstip}'}})
            MERGE (d)-[:ACTED]->(l)
            RETURN a
        ",
        "
            MERGE (a)-[:CURRENT]->(l:Log:Teiren{{userName: a.userName, eventName:'Login', eventResult: 'Success', eventTime:'{str(datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))}', sourceIp:'{srcip}', serverIp: '{dstip}'}})<-[:ACTED]-(b)
            RETURN a
        ",
        {{a:a, b:b, d:d}}
    ) YIELD value
    RETURN value.a.failCount
    """
    
    logger.debug(f'Executing query: {query}')
    
    try:
        auth_trigger = AuthTrigger()
        with auth_trigger.driver.session(database=db_name) as session:
            session.run(query)
    except Exception as e:
        logger.error(f'Error executing query: {e}')
    finally:
        auth_trigger.close()

    return 0

def login_fail(userName, srcip):
    try:
        user = get_user_model().objects.get(username=userName)
    except get_user_model().DoesNotExist:
        logger.error(f'User not found: {userName}')
        return 0

    db_name = user.db_name
    dstip = get_server_ip()
    
    query = f"""
    MATCH (a:Account:Teiren {{
        userName: '{userName}'
    }})
    SET a.failCount = a.failCount + 1
    WITH a
    OPTIONAL MATCH (a)-[:DATE]-(d:Date {{date:'{str(date.today())}'}})
    WITH a, d
    CALL apoc.do.when(
        d IS NULL,
        "MERGE (a)-[:DATE]->(d:Date {{date:'{str(date.today())}'}}) RETURN d",
        "MATCH (a)-[:DATE]->(d:Date {{date:'{str(date.today())}'}}) RETURN d",
        {{a:a}}
    ) YIELD value
    WITH a, value.d as d
    OPTIONAL MATCH (a)-[c:CURRENT]->(b:Log:Teiren)
    WHERE split(b.eventTime,'T')[0] = d.date
    WITH a, b, d
    OPTIONAL MATCH (a)-[c:CURRENT]->()
    DELETE c
    WITH a, b, d
    CALL apoc.do.when(
        b IS NULL,
        "
            MERGE (a)-[:CURRENT]->(l:Log:Teiren{{userName: a.userName, eventName:'Login', eventResult: 'Fail', eventTime:'{str(datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))}', sourceIp:'{srcip}', serverIp: '{dstip}'}})
            MERGE (d)-[:ACTED]->(l)
            RETURN a
        ",
        "
            MERGE (a)-[:CURRENT]->(l:Log:Teiren{{userName: a.userName, eventName:'Login', eventResult: 'Fail', eventTime:'{str(datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))}', sourceIp:'{srcip}', serverIp: '{dstip}'}})<-[:ACTED]-(b)
            RETURN a
        ",
        {{a:a, b:b, d:d}}
    ) YIELD value
    RETURN value.a.failCount
    """
    
    logger.debug(f'Executing query: {query}')
    
    try:
        auth_trigger = AuthTrigger()
        with auth_trigger.driver.session(database=db_name) as session:
            failCount = session.run(query)
    except Exception as e:
        logger.error(f'Error executing query: {e}')
        failCount = 0
    finally:
        auth_trigger.close()
        
    return failCount

@receiver(user_logged_out)
def logout_success(sender, request, **kwargs):
    db_name = request.session.get('db_name')
    dstip = get_server_ip()
    
    query = f"""
    MATCH (a:Account:Teiren {{
        userName: '{request.user}'
    }})
    WITH a
    OPTIONAL MATCH (a)-[:DATE]-(d:Date {{date:'{str(date.today())}'}})
    WITH a, d
    CALL apoc.do.when(
        d IS NULL,
        "MERGE (a)-[:DATE]->(d:Date {{date:'{str(date.today())}'}}) RETURN d",
        "MATCH (a)-[:DATE]->(d:Date {{date:'{str(date.today())}'}}) RETURN d",
        {{a:a}}
    ) YIELD value
    WITH a, value.d as d
    OPTIONAL MATCH (a)-[c:CURRENT]->(b:Log:Teiren)
    WHERE split(b.eventTime,'T')[0] = d.date
    WITH a, b, d
    OPTIONAL MATCH (a)-[c:CURRENT]->()
    DELETE c
    WITH a, b, d
    CALL apoc.do.when(
        b IS NULL,
        "
            MERGE (a)-[:CURRENT]->(l:Log:Teiren{{userName: a.userName, eventName:'Logout', eventResult: 'Success', eventTime:'{str(datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))}', sourceIp:'{get_client_ip(request)}', serverIp: '{dstip}'}})
            MERGE (d)-[:ACTED]->(l)
            RETURN a
        ",
        "
            MERGE (a)-[:CURRENT]->(l:Log:Teiren{{userName: a.userName, eventName:'Logout', eventResult: 'Success', eventTime:'{str(datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))}', sourceIp:'{get_client_ip(request)}', serverIp: '{dstip}'}})<-[:ACTED]-(b)
            RETURN a
        ",
        {{a:a, b:b, d:d}}
    ) YIELD value
    RETURN value.a
    """
    
    logger.debug(f'Executing query: {query}')
    
    try:
        auth_trigger = AuthTrigger()
        with auth_trigger.driver.session(database=db_name) as session:
            session.run(query)
    except Exception as e:
        logger.error(f'Error executing query: {e}')
    finally:
        auth_trigger.close()
