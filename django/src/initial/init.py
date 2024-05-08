from django.conf import settings
from neo4j import GraphDatabase
from init_node_list import init_merge_detect_query


URL = f"ndoe://{settings.NEO4J['HOST']}:{settings.NEO4J['PORT']}"
USER = settings.NEO4J['USERNAME']
PW = settings.NEO4J['PASSWORD']

def create_initial_detect_node(session):
    for cypher in init_merge_detect_query:
        try:
            session.run(cypher)
        except:
            print(f"{cypher} can't running")

def create_init_elb_node(session):
    cypher = """
    MERGE (node:Elb:Sub)
    SET node.name = 'Elb'
    RETURN node
    """
    try:
        session.run(cypher)
    except:
        print(f"{cypher} can't running")
    
if __name__ == '__main__':
    with GraphDatabase.driver(URL, auth=(USER, PW)) as driver:
        with driver.session() as session:
            create_initial_detect_node(session)
            create_init_elb_node(session)