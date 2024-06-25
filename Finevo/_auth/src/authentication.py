# local
import requests
from datetime import datetime, date
from common.neo4j.handler import Neo4jHandler

# django
from django.conf import settings
from django.contrib.auth.signals import user_logged_out
from django.contrib.auth import get_user_model
from django.dispatch import receiver

# 3rd party
from neo4j import GraphDatabase

# AWS
HOST = settings.NEO4J['HOST']
PORT = settings.NEO4J["PORT"]
USER = settings.NEO4J['USERNAME']
PW = settings.NEO4J['PASSWORD']

URI = f"bolt://{settings.NEO4J['HOST']}:{settings.NEO4J['PORT']}"


class AuthTrigger(Neo4jHandler):
    def __init__(self) -> None:
        super().__init__()

def login_success(userName, srcip, db_name):
    dstip = get_server_ip()
    query = f"""
    MATCH (a:Account:Teiren{{
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
    with GraphDatabase.driver(URI, auth=(USER, PW)) as driver:
        with driver.session(database=db_name) as session:
            session.run(query)
            
    return 0

def login_fail(userName, srcip):
    user = get_user_model().objects.get(username=userName)
    db_name = user.db_name
    dstip = get_server_ip()
    
    query = f"""
    MATCH (a:Account:Teiren{{
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
    with GraphDatabase.driver(URI, auth=(USER, PW)) as driver:
        with driver.session(database=db_name) as session:
            failCount = session.run(query)
            
    return failCount

@receiver(user_logged_out)
def logout_success(sender, request, **kwargs):
    db_name = request.session.get('db_name')
    with GraphDatabase.driver(URI, auth=(USER, PW)) as driver:
        with driver.session(database=db_name) as session:
            srcip = get_client_ip(request)
            dstip = get_server_ip()
            
            query = f"""
            MATCH (a:Account:Teiren{{
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
                    MERGE (a)-[:CURRENT]->(l:Log:Teiren{{userName: a.userName, eventName:'Logout', eventResult: 'Success', eventTime:'{str(datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))}', sourceIp:'{srcip}', serverIp: '{dstip}'}})
                    MERGE (d)-[:ACTED]->(l)
                    RETURN a",
                "
                    MERGE (a)-[:CURRENT]->(l:Log:Teiren{{userName: a.userName, eventName:'Logout', eventResult: 'Success', eventTime:'{str(datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))}', sourceIp:'{srcip}', serverIp: '{dstip}'}})<-[:ACTED]-(b)
                    RETURN a
                ",
                {{a:a, b:b, d:d}}
            ) YIELD value
            RETURN value
            """
            session.run(query)
            return 0

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_server_ip():
    try:
        dstip = requests.get('http://169.254.169.254/latest/meta-data/public-ipv4', timeout=2).text
    except requests.exceptions.RequestException:
        dstip = '127.0.0.1'
    return dstip