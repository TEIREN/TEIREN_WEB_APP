from django.shortcuts import render, redirect, HttpResponse
from django.conf import settings
from py2neo import Graph, ClientError
# import json
import math
import itertools
# from datetime import datetime
# from django.utils import timezone
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
# graph = Graph(f"bolt://{host}:7688", auth=(username, password))

def get_log_page(request, logType):
    # print(request)
    #페이징
    try:
        if 'page' in request:
            now_page = int(request['page'][0])  # 페이지
        else:
            raise ValueError
    except ValueError:
        now_page = 1
    except TypeError:
        now_page = 1
    filter_check = 0
    if logType == 'filter':
        filter_check = 1
        logType = request.pop('logType')[0].split(' ')[0]
    
    #Filtering
    filter_dict = {}
    for key, value in request.items():
        if key == 'page' or key.endswith('regex') or value[0] == 'all': continue
        if 'main' in filter_dict and key in filter_dict['main']:
            continue
        if len(value) == 1 and value[0] == '':
            continue
        if key.startswith('main'):
            if request['main_search_value'][0] != '':
                filter_dict['main'] = [request['main_search_key'][0],request['main_search_value'][0]]
            continue
        if value[0] == 'regex':
            value.append(request[f'{key}_regex'][0])
        if key.startswith('eventTime'):
            filter_dict['eventTime'] = [request['eventTime_date_start'][0],request['eventTime_date_end'][0]]
            continue
        filter_dict[key] = value

    where_dict = create_where_dict(filter_dict)
    
    # Creating Where Cypher
    where_cypher = 'WHERE '
    for cnt in range(len(where_dict)):
        key, filter = next(itertools.islice(where_dict.items(), cnt, None))
        where_cypher += '('
        if key == 'logTypes':
            for value in filter['value']:
                where_cypher += f"'{value}' IN LABELS(n) OR "
        elif key == 'eventTime':
            start_time = f"'{filter['value'][0]}'"
            end_time = f"'{filter['value'][1]}'"
            for prop in filter['key']:
                where_cypher += f"{start_time + '<=' if len(start_time) > 2 else ''} n.{prop} {'<=' + end_time if len(end_time) > 2 else ''} OR "
        else:
            for prop in filter['key']:
                if filter['value'][0] == 'regex':
                    value = filter['value'][1]
                    where_cypher += f"n.{prop} =~ '.*{value}.*' OR "
                else:
                    for value in filter['value']:
                        where_cypher += f"n.{prop} = '{value}' OR "
        where_cypher = where_cypher[:-4] + ') AND '
        if cnt == len(where_dict)-1:
            where_cypher = where_cypher[:-5]

    #페이지당 보여줄 로그 개수
    limit = 10
    cypher = f"""
    MATCH (n:Log:{logType.capitalize()})
    {where_cypher if len(where_cypher) > 6 else ''}
    WITH n
    ORDER BY n.eventTime DESC, n.request_creation_time DESC, n.timestamp DESC
    SKIP {(now_page-1)*limit}
    LIMIT {limit}
    RETURN
        id(n) AS id,
        CASE
            WHEN [label in labels(n) WHERE NOT label IN ['{logType.capitalize()}', 'Log']][0] IS NOT NULL THEN  [label in labels(n) WHERE NOT label IN ['{logType.capitalize()}', 'Log']][0]
            ELSE '{logType.capitalize()}'
        END AS logTypes,
        CASE
            WHEN n.eventTime IS NOT NULL THEN apoc.date.format(apoc.date.parse(n.eventTime, "ms", "yyyy-MM-dd'T'HH:mm:ssX"), "ms", "yyyy-MM-dd HH:mm:ss")
            WHEN n.request_creation_time IS NOT NULL THEN n.request_creation_time
            WHEN n.timestamp IS NOT NULL THEN n.timestamp
        END AS eventTime,
        CASE
            WHEN n.eventName IS NOT NULL THEN n.eventName
            WHEN n.queryType IS NOT NULL THEN n.queryType
            WHEN n.type IS NOT NULL THEN n.type
            ELSE '-'
        END AS eventType,
        CASE
            WHEN n.userIdentity_arn IS NOT NULL THEN n.userIdentity_arn
            WHEN n.resources_1_ARN IS NOT NULL THEN n.resources_1_ARN
            WHEN n.client_port IS NOT NULL THEN n.client_port
            WHEN n.userName IS NOT NULL THEN n.userName
            ELSE '-'
        END AS source,
        CASE
            WHEN n.eventSource IS NOT NULL THEN n.eventSource
            WHEN n.queryName IS NOT NULL THEN n.queryName
            WHEN n.elb IS NOT NULL THEN n.elb
            ELSE '-'
        END AS destination,
        CASE
            WHEN n.errorCode IS NOT NULL THEN n.errorCode
            WHEN n.eventType IS NOT NULL THEN n.eventType
            WHEN n.responseCode IS NOT NULL THEN n.responseCode
            WHEN n.actions_executed IS NOT NULL THEN n.actions_executed+' > '+n.redirect_url
            WHEN n.eventResult IS NOT NULL THEN n.eventResult
            ELSE '-'
        END AS eventResult,
        CASE
            WHEN n.sourceIPAddress IS NOT NULL THEN n.sourceIPAddress
            WHEN toString(n.client_port) IS NOT NULL THEN n.client_port
            WHEN n.sourceIp IS NOT NULL THEN n.sourceIp
            ELSE '-'
        END AS srcIp,
        CASE
            WHEN n.resolverIp IS NOT NULL THEN n.resolverIp
            WHEN n.request IS NOT NULL THEN n.request
            WHEN n.serverIp IS NOT NULL THEN n.serverIp
            ELSE '-'
        END AS dstIp,
        '{logType.capitalize()}' AS logType
    """
    log_list = []
    try:
        if graph.evaluate(cypher) is None:
            raise ClientError('','Neo.3.0.3')
        results = graph.run(cypher)
        for result in results:
            log_list.append(dict(result))
    except ClientError:
        return {'error': 'No Data'}

    page_obj={'log_list': log_list}
    page_obj['test'] = cypher
    #총 로그 개수
    total_log = graph.evaluate(f"""
        MATCH (n:Log:{logType.capitalize()})
        {where_cypher if len(where_cypher) > 6 else ''}
        RETURN COUNT(n)
    """)
    total_page = math.ceil(total_log / limit)
    st_page = max(1, now_page - 5)
    ed_page = min(total_page, now_page + 5)

    # if ed_page < 10:
    #     ed_page=10
    page_obj['has_previous'] = True if now_page > 1 else False
    page_obj['previous_page_number']=now_page-1
    page_obj['paginator'] = {'page_range': range(st_page, ed_page+1)}
    page_obj['now_page']=now_page
    page_obj['has_next'] = True if now_page < total_page else False
    page_obj['next_page_number']=now_page+1
    page_obj['paginator']['num_pages']=total_page
    
    if filter_check:
        response = {
            'page_obj': page_obj,
            'current_log': [((now_page-1)*10)+1, (now_page*10 if total_log > now_page*10 else total_log)],
            'total_log': total_log
        }
        return response
    
    response = {
        'page_obj': page_obj,
        'total_log': total_log,
        'current_log': [((now_page-1)*10)+1, now_page*10 if now_page*10 < total_log else total_log]
    }
    response.update(create_filter_list(logType))
    # print(response)
    return response

def create_where_dict(filter_dict):
    where_dict = {}
    for key, value in filter_dict.items():
        ## If main search -> change to regex
        if key == 'main':
            key = value[0]
            value[0] = 'regex'

        where_dict[key] = {}
        if key == 'logTypes':
            pass
        elif key == 'eventTime':
            where_dict[key]['key'] = ['eventTime', 'timestamp', 'request_creation_time', 'eventTime']
        elif key == 'eventType':
            where_dict[key]['key'] = ['eventName', 'queryType', 'type', 'eventName']
        elif key == 'source':
            where_dict[key]['key'] = ['userIdentity_arn', 'client_port', 'sourceIp']
        elif key == 'destination':
            where_dict[key]['key'] = ['eventSource', 'queryname', 'elb', 'serverIp']
        elif key == 'eventResult':
            where_dict[key]['key'] = ['errorCode', 'eventType', 'responseCode', 'actions_executed', 'eventResult']
        elif key == 'srcIp':
            where_dict[key]['key'] = ['sourceIPAddress', 'client_port', 'sourceIp']
        elif key == 'dstIp':
            where_dict[key]['key'] = ['resolverIp', 'request', 'serverIp']
        where_dict[key]['value'] = value
    return where_dict

def create_filter_list(logType):
    #LogType list
    logType_list = graph.evaluate(f"""
    MATCH (n:Log:{logType.capitalize()})
    UNWIND labels(n) as label
    WITH DISTINCT(label) WHERE NOT label IN ['{logType.capitalize()}', 'Log']
    RETURN COLLECT(label)
    """)

    #EventType list
    eventType_list = graph.evaluate(f"""
    MATCH (n:Log:{logType.capitalize()})
    WITH CASE
        WHEN n.eventName IS NOT NULL THEN n.eventName
        WHEN n.queryType IS NOT NULL THEN n.queryType
        WHEN n.type IS NOT NULL THEN n.type
        ELSE '-'
    END AS eventType
    WITH DISTINCT(eventType) WHERE eventType <> '-'
    RETURN COLLECT(eventType)
    """)

    #Source listCASE
    source_list = graph.evaluate(f"""
    MATCH (n:Log:{logType.capitalize()})
    WITH CASE
        WHEN n.userIdentity_arn IS NOT NULL THEN n.userIdentity_arn
        WHEN n.resources_1_ARN IS NOT NULL THEN n.resources_1_ARN
        WHEN n.client_port IS NOT NULL THEN n.client_port
        WHEN n.userName IS NOT NULL THEN n.userName
        ELSE '-'
    END AS source
    WITH DISTINCT(source) WHERE source <> '-'
    RETURN COLLECT(source)
    """)

    #Destination list 검색
    destination_list = graph.evaluate(f"""
    MATCH (n:Log:{logType.capitalize()})
    WITH CASE
        WHEN n.eventSource IS NOT NULL THEN n.eventSource
        WHEN n.queryName IS NOT NULL THEN n.queryName
        WHEN n.elb IS NOT NULL THEN n.elb
        ELSE '-'
    END AS destination
    WITH DISTINCT(destination) WHERE destination <> '-'
    RETURN COLLECT(destination)
    """)

    # EventResult list 검색
    eventResult_list = graph.evaluate(f"""
    MATCH (n:Log:{logType.capitalize()})
    WITH CASE
        WHEN n.errorCode IS NOT NULL THEN n.errorCode
        WHEN n.eventType IS NOT NULL THEN n.eventType
        WHEN n.responseCode IS NOT NULL THEN n.responseCode
        WHEN n.actions_executed IS NOT NULL THEN n.actions_executed+' > '+n.redirect_url
        WHEN n.eventResult IS NOT NULL THEN n.eventResult
        ELSE '-'
    END AS eventResult
    WITH DISTINCT(eventResult) WHERE eventResult <> '-'
    RETURN COLLECT(eventResult)
    """)

    # SrcIp list 검색
    srcIp_list = graph.evaluate(f"""
    MATCH (n:Log:{logType.capitalize()})
    WITH CASE
        WHEN n.sourceIPAddress IS NOT NULL THEN n.sourceIPAddress
        WHEN toString(n.client_port) IS NOT NULL THEN n.client_port
        WHEN n.sourceIp IS NOT NULL THEN n.sourceIp
        ELSE '-'
    END AS srcIp
    WITH DISTINCT(srcIp) WHERE srcIp <> '-'
    RETURN COLLECT(srcIp)
    """)

    # DstIp list 검색
    dstIp_list = graph.evaluate(f"""
    MATCH (n:Log:{logType.capitalize()})
    WITH CASE
        WHEN n.resolverIp IS NOT NULL THEN n.resolverIp
        WHEN n.request IS NOT NULL THEN n.request
        WHEN n.serverIp IS NOT NULL THEN n.serverIp
        ELSE '-'
    END AS dstIp
    WITH DISTINCT(dstIp) WHERE dstIp <> '-'
    RETURN COLLECT(dstIp)
    """)

    response = {
        'logType_list':logType_list,
        'eventType_list':eventType_list,
        'source_list': source_list,
        'destination_list': destination_list,
        'eventResult_list': eventResult_list,
        'srcIp_list': srcIp_list,
        'dstIp_list': dstIp_list
    }
    return response

# 로그 디테일 모달
def get_log_detail_modal(request):
    id = request['id']
    logType = request['logType']
    cypher = f"""
    MATCH (l:Log:{logType})
    WHERE ID(l) = {id}
    WITH ID(l) as id, PROPERTIES(l) as details
    RETURN id, details
    """
    results = graph.run(cypher)
    response = {}
    for result in results:
        for key, value in dict(result).items():
            if key == 'details':
                value = {keys:value[keys] for keys in sorted(value.keys())}
            response[key] = value
    return response