from django.conf import settings

from neo4j import GraphDatabase
from common.neo4j.handler import Neo4jHandler

## AWS
host = settings.NEO4J['HOST']
port = settings.NEO4J["PORT"]
username = settings.NEO4J['USERNAME']
password = settings.NEO4J['PASSWORD']
uri = f"bolt://{host}:{port}"


class TopbarAlerm(Neo4jHandler):
    def __init__(self) -> None:
        super().__init__()
    
    def check_topbar_alert(self, db_name):
        cypher = """
        MATCH (r:Rule)<-[d:DETECTED|FLOW_DETECTED]-()
        WHERE d.alert = 0 OR d.alert IS NULL
        SET d.alert = CASE
                WHEN d.alert IS NULL THEN 0
                ELSE d.alert
            END
        RETURN COUNT(d) as count
        """

def do_cypher_tx(tx, cypher):
    result = tx.run(cypher)
    node = result.single()
    
    return node.get('node') if node else None

# Top Bar 알림
def check_topbar_alert(db_name):
    with GraphDatabase.driver(uri, auth=(username, password)) as driver:
        with driver.session(database=db_name) as session:
            query = """
            MATCH (r:Rule)<-[d:DETECTED|FLOW_DETECTED]-()
            WHERE d.alert = 0 OR d.alert IS NULL
            SET d.alert = CASE
                    WHEN d.alert IS NULL THEN 0
                    ELSE d.alert
                END
            RETURN COUNT(d) as count
            """
            result = session.run(query)
            count = result.single()[0]
            if count > 0:
                response = {'top_alert':{'count': count}}
                query2 = """
                MATCH (r:Rule)<-[d:DETECTED|FLOW_DETECTED]-(l:Log)
                WHERE d.sent = 0 OR d.sent IS NULL
                WITH DISTINCT(d) as d, r, l
                SET d.sent = CASE
                        WHEN d.sent IS NULL THEN 0
                        ELSE d.sent
                    END
                RETURN r, l, ID(d) as id_d
                """
                results = session.execute_write(do_cypher_tx, query2)
                if results is not None:
                    for result in results:
                        query3 = f"""
                        MATCH (r:Rule)<-[d:DETECTED|FLOW_DETECTED]-(l:Log)
                        WHERE ID(r) = {result['r'].identity} AND
                            ID(l) = {result['l'].identity} AND
                            ID(d) = {result['id_d']} AND
                            (d.sent = 0 OR d.sent IS NULL)
                        SET d.sent = 1
                        RETURN count(d)
                        """
                        session.execute_write(do_cypher_tx, query3)
                        send_alert_mail(dict(result['r']), dict(result['l']), result['id_d'])
            else:
                response = {'no_top_alert': 1}
            return response

# 알림 메일
def send_alert_mail(rule, log, rel_id):
    return 1
    # subject = f"Teiren SIEM Rule Detection Alert Mail [{rule['ruleName']}#{rel_id}]"
    # message = ''
    # from_email = settings.EMAIL_HOST_USER
    # recipient_list = ['chosomang12@gmail.com']
    # context = {
    #     'r': rule,
    #     'rel_id': rel_id,
    #     'l': log,
    # }
    # html_message = render_to_string('risk/alert/mail.html', context)
    # send_mail(subject, message, from_email, recipient_list, html_message=html_message)
