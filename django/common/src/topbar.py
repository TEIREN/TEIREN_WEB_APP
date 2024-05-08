from django.conf import settings
from py2neo import Graph

## AWS
host = settings.NEO4J['HOST']
port = settings.NEO4J["PORT"]
username = settings.NEO4J['USERNAME']
password = settings.NEO4J['PASSWORD']
graph = Graph(f"bolt://{host}:{port}", auth=(username, password))

# Top Bar 알림
def check_topbar_alert():
    global graph
    cypher = """
    MATCH (r:Rule)<-[d:DETECTED|FLOW_DETECTED]-()
    WHERE d.alert = 0 OR d.alert IS NULL
    SET d.alert = CASE
            WHEN d.alert IS NULL THEN 0
            ELSE d.alert
        END
    RETURN COUNT(d) as count
    """
    count = graph.evaluate(cypher)
    if count > 0:
        response = {'top_alert':{'count': count}}
        cypher = """
        MATCH (r:Rule)<-[d:DETECTED|FLOW_DETECTED]-(l:Log)
        WHERE d.sent = 0 OR d.sent IS NULL
        WITH DISTINCT(d) as d, r, l
        SET d.sent = CASE
                WHEN d.sent IS NULL THEN 0
                ELSE d.sent
            END
        RETURN r, l, ID(d) as id_d
        """
        if graph.evaluate(cypher) is not None:
            results = graph.run(cypher)
            for result in results:
                cypher = f"""
                MATCH (r:Rule)<-[d:DETECTED|FLOW_DETECTED]-(l:Log)
                WHERE ID(r) = {result['r'].identity} AND
                    ID(l) = {result['l'].identity} AND
                    ID(d) = {result['id_d']} AND
                    (d.sent = 0 OR d.sent IS NULL)
                SET d.sent = 1
                RETURN count(d)
                """
                graph.evaluate(cypher)
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
