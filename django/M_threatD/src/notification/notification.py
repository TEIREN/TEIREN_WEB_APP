from django.shortcuts import render, HttpResponse
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.http import QueryDict
from py2neo import Graph
from datetime import date
import json
import math


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

def get_alert_logs(request):
    filter_dict = {}
    if 'filter' in request:
        for item in json.loads(request['filter'][0]):
            if item['name'] in filter_dict:
                filter_dict[item['name']].append(item['value'])
            else:
                filter_dict[item['name']] = [item['value']]
    
    # order_list
    order_list = [] if 'order' not in request else request.pop('order')
    order_cypher = 'ORDER BY '
    if len(order_list) < 1:
        order_cypher += 'alert, eventTime DESC, rlevel DESC'
    else:
        order_cypher += f"{order_list[0]} {order_list[1]}"
        if order_list[0] not in ['sourceIp']:
            for check_order in ['eventTime', 'rlevel']:
                if order_list[0] != check_order:
                    order_cypher += f", {check_order} DESC"
    
    # limit & page
    for key in ['limit', 'page']:
        try:
            if key in request:
                filter_dict[key] = int(request[key][0])
            else:
                raise ValueError
        except (ValueError, TypeError):
            if key == 'limit':
                filter_dict[key] = 10
            elif key == 'page':
                filter_dict[key] = 1
    limit = filter_dict.pop('limit')
    page = filter_dict.pop('page')

    # filtering
    where_dict = {}
    for key, value in filter_dict.items():
        if value[0] == '' or value[0] == 'all' or key in ['main_search_value'] or key in where_dict or key.endswith('regex'):
            continue
        elif key == 'main_search_key':
            if filter_dict['main_search_value'][0] != '':
                print(filter_dict['main_search_value'])
                where_dict[value[0]] = ['regex', f".*{filter_dict['main_search_value'][0]}.*"]
        elif key.startswith('eventTime'):
            if any(time != '' for time in [filter_dict['eventTime_date_start'][0], filter_dict['eventTime_date_end'][0]]):
                where_dict['eventTime'] = [filter_dict['eventTime_date_start'][0], filter_dict['eventTime_date_end'][0]]
        elif value[0] == 'regex':
            where_dict[key] = ['regex', filter_dict[f'{key}_regex'][0]]
        else:
            where_dict[key] = value
    # where cypher
    where_cypher = 'WHERE '
    for key, value in where_dict.items():
        if len(where_cypher) != 6:
            where_cypher += ' AND '
        if key == 'eventTime':
            where_cypher += f"""{f"'{value[0]}'>= " if value[0] != '' else ''}eventTime{f" <='{value[0]}'" if value[0] != '' else ''}"""
        elif value[0] == 'regex':
            where_cypher += f"{key} =~ '{value[1]}'"
        elif key == 'severity':
            where_cypher += '('
            for val in value:
                where_cypher += f"{key} = {val} OR "
            where_cypher = where_cypher[:-3]+')'
        else:
            where_cypher += '('
            for val in value:
                where_cypher += f"{key} = '{val}' OR "
            where_cypher = where_cypher[:-4]+')'
    cypher = f"""
    MATCH (l:Log)-[d:DETECTED|FLOW_DETECTED]->(r:Rule)
    WITH
        r.level as rlevel,
        HEAD([label IN labels(r) WHERE label <> 'Rule']) AS resource,
        l.eventTime as eventTime,
        l.eventTime AS eventTime_format,
        r.ruleComment as ruleComment,
        l.eventName as eventName,
        CASE
            WHEN r.level = 1 THEN ['LOW', 'success']
            WHEN r.level = 2 THEN ['MID', 'warning']
            WHEN r.level = 3 THEN ['HIGH', 'caution']
            ELSE ['CRITICAL', 'danger']
        END AS severity,
        CASE
            WHEN toString(l.sourceIPAddress) IS NOT NULL THEN l.sourceIPAddress
            WHEN toString(l.sourceIp) IS NOT NULL THEN l.sourceIp
            ELSE '-'
        END AS sourceIp,
        CASE
            WHEN toString(l.sourceIPAddress) IS NOT NULL THEN toInteger(split(l.sourceIPAddress, '.')[0])
            WHEN toString(l.sourceIp) IS NOT NULL THEN toInteger(split(l.sourceIp, '.')[0])
            ELSE '-'
        END AS ip,
        r.ruleName as detected_rule,
        r.ruleClass as rule_class,
        r.ruleName+'#'+id(d) AS rule_name,
        ID(d) as id,
        CASE
            WHEN d.alert <> 1 THEN 0
            WHEN d.alert IS NULL THEN 0
            ELSE 1
        END AS alert
    {where_cypher if len(where_cypher)>6 else ''}
    """
    results = graph.run(f"""
    {cypher}
    RETURN resource, eventTime, eventTime_format, ruleComment, eventName, severity, sourceIp, detected_rule, rule_class, rule_name, id, alert
    {order_cypher}
    SKIP {(page-1)*limit}
    LIMIT {limit}
    """)
    data = []
    filter = ['resource', 'detected_rule', 'eventTime', 'rule_name', 'alert', 'id', 'rule_class']
    for result in results:
        detail = dict(result.items())
        form = {}
        for key in filter:
            if key not in ['resource', 'rule_name', 'alert']:
                value = detail.pop(key)
            else:
                value = detail[key]
            form[key] = value
        detail['form'] = form
        data.append(detail)
    
    total_count = graph.evaluate(f"""
    {cypher}
    RETURN COUNT(id)
    """)
    page_obj = {}
    total_page = math.ceil(total_count / limit)
    st_page = max(1, page - 3)
    ed_page = min(total_page, page + 3 if page > 4 else 7)
    page_obj['has_previous'] = True if page > 1 else False
    page_obj['previous_page_number']=page-1
    page_obj['paginator'] = {'page_range': range(st_page, ed_page+1)}
    page_obj['cur_page']=page
    page_obj['has_next'] = True if page < total_page else False
    page_obj['next_page_number']=page+1
    page_obj['paginator']['num_pages']=total_page

    response = {
        'data': data,
        'total_count': total_count,
        'current_count': [((page-1)*10)+1, (page*10 if total_count > page*10 else total_count)],
        'page_obj': page_obj
    }

    print([((page-1)*10)+1, (page*10 if total_count > page*10 else total_count)])
    print(total_count)
    return response


def get_filter_list():
    resource_list = graph.evaluate(f"""
    MATCH (l:Log)-[d:DETECTED|FLOW_DETECTED]->(r:Rule)
    WITH HEAD([label IN labels(r) WHERE label <> 'Rule']) AS resource
    RETURN COLLECT(DISTINCT(resource))
    """)

    eventName_list = graph.evaluate(f"""
    MATCH (l:Log)-[d:DETECTED|FLOW_DETECTED]->(r:Rule)
    WITH DISTINCT(l.eventName) AS eventName
    RETURN COLLECT(eventName)
    """)
    response = {
        'resource_list': resource_list,
        'eventName_list': eventName_list
    }
    return response

# Top Bar 알림
def check_topbar_alert():
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
    print(request)
    if 'alert' in request:
        graph.evaluate(f"""
        MATCH (r:Rule:{request['resource']} {{ruleName:'{request['detected_rule']}'}})<-[d:DETECTED|FLOW_DETECTED]-(l:Log:{request['resource']} {{eventTime:'{request['eventTime']}'}})
        WHERE
            d.alert IS NOT NULL AND
            d.alert = 0 AND
            ID(d) = {request['id']}
        SET d.alert = 1
        RETURN count(d.alert)
        """)
    return request

