from django.shortcuts import render, HttpResponse
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from py2neo import Graph
import json
from datetime import date

## LOCAL
# graph = Graph("bolt://127.0.0.1:7687", auth=('neo4j', 'teiren001'))

## NCP
# host = settings.NEO4J_HOST
# port = settings.NEO4J_PORT
# password = settings.NEO4J_PASSWORD
# username = settings.NEO4J_USERNAME

## AWS
host = settings.NEO4J['HOST']
port = settings.NEO4J["PORT"]
username = settings.NEO4J['USERNAME']
password = settings.NEO4J['PASSWORD']
graph = Graph(f"bolt://{host}:{port}", auth=(username, password))

def get_alert_logs():
    global graph
    cypher = '''
    MATCH (l:Log)-[d:DETECTED|FLOW_DETECTED]->(r:Rule)
    WHERE
        d.alert = 1 AND d.alert IS NOT NULL
    RETURN
        HEAD([label IN labels(r) WHERE label <> 'Rule']) AS cloud,
        l.eventTime AS detected_time,
        r.ruleComment as detectedAction,
        l.eventName as actionDisplayName,
        l.eventType as actionResultType,
        l.eventTime as eventTime,
        l.eventTime AS eventTime_format,
        l.sourceIPAddress as sourceIp,
        r.ruleName as detected_rule,
        r.ruleClass as rule_class,
        r.ruleName+'#'+id(d) AS rule_name,
        ID(d) as id
    ORDER BY eventTime DESC
    '''
    results = graph.run(cypher)
    data = check_alert_logs()
    filter = ['cloud', 'detected_rule', 'eventTime', 'rule_name', 'id', 'rule_class']
    for result in results:
        detail = dict(result.items())
        form = {}
        for key in filter:
            if key != 'cloud' and key != 'rule_name':
                value = detail.pop(key)
            else:
                value = detail[key]
            form[key] = value
        detail['form'] = form
        data.append(detail)
    context = {'data': data}
    return context

def check_alert_logs():
    global graph
    cypher = """
    MATCH (l:Log)-[d:DETECTED|FLOW_DETECTED]->(r:Rule)
    WHERE
        d.alert <> 1
    RETURN
        HEAD([label IN labels(r) WHERE label <> 'Rule']) AS cloud,
        l.eventTime AS detected_time,
        r.ruleComment AS detectedAction,
        l.eventName AS actionDisplayName,
        l.eventType AS actionResultType,
        l.eventTime AS eventTime,
        l.eventTime AS eventTime_format,
        l.sourceIPAddress AS sourceIp,
        r.ruleName AS detected_rule,
        r.ruleName+'#'+id(d) AS rule_name,
        r.ruleClass as rule_class,
        ID(d) AS id,
        d.alert AS alert
    ORDER BY alert, eventTime DESC
    """
    results = graph.run(cypher)
    data = []
    filter = ['cloud', 'detected_rule', 'eventTime', 'rule_name', 'alert', 'id', 'rule_class']
    for result in results:
        detail = dict(result.items())
        form = {}
        for key in filter:
            if key != 'cloud' and key != 'rule_name' and key != 'alert':
                value = detail.pop(key)
            else:
                value = detail[key]
            form[key] = value
        detail['form'] = form
        data.append(detail)
    return data

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

# 위협 알림 확인 후 Alert Off
def alert_off(request):
    if 'alert' in request:
        detected_rule = request['detected_rule']
        cloud = request['cloud']
        eventTime = request['eventTime']
        id = request['id']
        if cloud == 'Aws':
            cypher = f"""
            MATCH (r:Rule:{cloud} {{ruleName:'{detected_rule}'}})<-[d:DETECTED|FLOW_DETECTED]-(l:Log:{cloud} {{eventTime:'{eventTime}'}})
            WHERE
                d.alert IS NOT NULL AND
                d.alert = 0 AND
                ID(d) = {id}
            SET d.alert = 1
            RETURN count(d.alert)
            """
        graph.evaluate(cypher)
    return request

