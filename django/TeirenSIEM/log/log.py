from django.shortcuts import render, redirect, HttpResponse
from django.conf import settings
from py2neo import Graph, ClientError
import json
import math
from datetime import datetime
from django.utils import timezone
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

def get_log_page(request, cloud):
    #페이징
    try:
        if 'page' in request:
            now_page = int(request['page'])  # 페이지
        else:
            raise ValueError
    except ValueError:
        now_page = 1
    except TypeError:
        now_page = 1
    # return {'error': str(request)}
    filter_check = 0
    if cloud == 'filter':
        filter_check = 1
        cloud = request.pop('cloud')
    # return {'error': str(request)}
    table_filter = {}
    for key in request:
        if key == 'page': continue
        if key.split('_')[0] == 'region':
            filter_key = 'awsRegion'
        elif key.split('_')[0] == 'user':
            filter_key = 'userIdentity_userName'
        else:
            filter_key = key.split('_')[0]
        if filter_key not in table_filter:
            table_filter[filter_key] = []
        filter_value = key.split('_')[1]
        if filter_value == 'regex':
            if request[key]:
                filter_value = 'regex:' + request[key]
            else: continue
        if filter_value == 'date':
            if request[key]:
                filter_value = f"{key.split('_', 1)[1]}:{request[key]}"
            else: continue
        table_filter[filter_key].append(filter_value)
    # return {'error': str(table_filter)}

    where_cypher = 'WHERE '
    for key, filters in table_filter.items():
        if len(filters) < 1 or key == 'search': continue
        if 'all' in filters: filters.remove('all')
        for i in range(0,len(filters)):
            if filters[i]:
                if filters[i].startswith('regex:'):
                    if filters[i].split(':')[1]:
                        where_cypher += 'AND (' if i == 0 and len(where_cypher) > 6 else '('
                        where_cypher += f"n.{key} =~ '{filters[i].split(':')[1]}') "
                        break
                    else:
                        continue
                if filters[i].startswith('date'):
                    if filters[i].split(':')[1]:
                        where_cypher += 'AND (' if len(where_cypher) > 6 else '('
                        if filters[i].split(':')[0].split('_')[1] == 'start':
                            where_cypher += f"n.{key} >= '{filters[i].split(':')[1]}T00:00:01Z') "
                        else:
                            where_cypher += f"n.{key} <= '{filters[i].split(':')[1]}T23:59:59Z') "
                        continue
                    else:
                        continue
                where_cypher += 'AND ' if i == 0 and len(where_cypher) > 6 else ''
                where_cypher += '(' if i == 0 else ''
                where_cypher += 'OR ' if len(where_cypher) > 6 and i > 0 else ''
                if key == 'eventSource':
                    where_cypher += f"n.{key} = '{filters[i]}.amazonaws.com' "
                elif key == 'userIdentity_userName':
                    where_cypher += f"n.{key} = '{filters[i]}' OR n.userIdentity_type = '{filters[i]}' "
                else:
                    where_cypher += f"n.{key} = '{filters[i]}' "
                where_cypher += ') ' if len(where_cypher) > 6 and i == len(filters)-1 else ''
    #페이지당 보여줄 로그 개수
    limit = 10
    cypher = f"""
    MATCH (n:Log:{cloud.capitalize()})
    {where_cypher if len(where_cypher) > 6 else ''}
    WITH n
    ORDER BY n.eventTime DESC
    SKIP {(now_page-1)*limit}
    LIMIT {limit}
    RETURN
        id(n) AS id,
        apoc.date.format(apoc.date.parse(n.eventTime, "ms", "yyyy-MM-dd'T'HH:mm:ssX"), "ms", "yyyy-MM-dd HH:mm:ss") AS eventTime,
        n.eventName AS eventName,
        split(n.eventSource, '.')[0] AS eventSource,
        n.userIdentity_arn AS userarn,
        n.userIdentity_type AS userType,
        CASE
            WHEN n.userIdentity_type <> 'IAMUser' THEN n.userIdentity_type
            ELSE n.userIdentity_userName
        END AS userName,
        n.awsRegion AS awsRegion,
        split(n.responseElements_assumedRoleUser_arn, '/')[1] AS role,
        n.sourceIPAddress AS sourceIP,
        [label IN LABELS(n) WHERE NOT label IN ['Log', 'Iam', 'Ec2'] AND size(label) = 3][0] AS cloud
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
        MATCH (n:Log:{cloud.capitalize()})
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
            'total_log': total_log,
        }
        return response
    
    #상품 검색
    eventSource_list= graph.evaluate(f"""
    MATCH (n:Log:{cloud.capitalize()})
    WHERE n.eventSource IS NOT NULL
    WITH DISTINCT(split(n.eventSource, '.')[0]) AS eventSource
    ORDER BY eventSource
    RETURN COLLECT(eventSource)
    """)
    
    #유저 검색
    user_list=graph.evaluate(f"""
    MATCH (n:Log:{cloud.capitalize()})
    WHERE n.userIdentity_type IS NOT NULL
    WITH
        CASE
            WHEN n.userIdentity_type <> 'IAMUser' THEN n.userIdentity_type
            ELSE n.userIdentity_userName
        END AS user
    WITH DISTINCT(user)
    ORDER BY user
    RETURN COLLECT(user)
    """)

    #sourceIP 검색
    sourceIPAddress_list = graph.evaluate(f"""
    MATCH (n:Log:{cloud.capitalize()})
    WHERE n.sourceIPAddress IS NOT NULL
    WITH DISTINCT(n.sourceIPAddress) AS sourceIPAddress
    ORDER BY sourceIPAddress
    RETURN COLLECT(sourceIPAddress)
    """)

    # awsregion 검색
    region_list = graph.evaluate(f"""
    MATCH (n:Log:{cloud.capitalize()})
    WHERE n.awsRegion IS NOT NULL
    WITH DISTINCT(n.awsRegion) AS awsRegion
    ORDER BY awsRegion
    RETURN COLLECT(awsRegion)
    """)

    # eventName 검색
    eventName_list = graph.evaluate(f"""
    MATCH (n:Log:{cloud.capitalize()})
    WHERE n.eventName IS NOT NULL
    WITH DISTINCT(n.eventName) AS eventName
    ORDER BY eventName
    RETURN COLLECT(eventName)
    """)

    response = {
        'page_obj': page_obj,
        'eventSource_list':eventSource_list,
        'user_list':user_list,
        'total_log': total_log,
        'sourceIPAddress_list': sourceIPAddress_list,
        'region_list': region_list,
        'eventName_list': eventName_list,
        'current_log': [((now_page-1)*10)+1, now_page*10],
    }
    return response


# 로그 디테일 모달
def get_log_detail_modal(request):
    id = request['id']
    cloud = request['cloud']
    cypher = f"""
    MATCH (l:Log:{cloud})
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