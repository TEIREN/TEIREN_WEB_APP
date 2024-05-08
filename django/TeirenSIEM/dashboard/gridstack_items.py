from django.template.loader import render_to_string
from django.shortcuts import render, HttpResponse
from django.http import JsonResponse, HttpResponseRedirect
from django.conf import settings
from py2neo import Graph
import datetime
import json
import math
import psutil

# AWS
host = settings.NEO4J['HOST']
port = settings.NEO4J["PORT"]
username = settings.NEO4J['USERNAME']
password = settings.NEO4J['PASSWORD']
graph = Graph(f"bolt://{host}:{port}", auth=(username, password))



# 로그 Bar Chart Color 지정
def get_log_color(collection_name):
    response = ''
    color = {
        "Aws" : "#FF9900",
        "NCP" : "#1EC800",
        "NHN" : "#4E73DF",
        "OFFICEKEEPER" : "#0059A9",
        "WINDOWS_EVENT_LOG" : "#357EC7"
    }
    if collection_name in color:
        response = color[collection_name]
    else:
        return False
    return response

# 로그 총 개수
def logTotal(request):
    cypher = """
    MATCH (n:Log)
    RETURN COUNT(n) AS total
    """
    log_total = graph.evaluate(cypher)
    context = {"total": format(log_total, ",")}
    if isinstance(request, dict):
        return render_to_string('dashboard/items/logTotal.html',context, request['request'])
    response = {'w':2, 'content': render_to_string('dashboard/items/logTotal.html',context, request)}
    return JsonResponse(response)

# 연동된 제품 개수
def integrationTotal(request):
    cypher = f"""
    MATCH (i:Integration)
    RETURN count(i)
    """
    total = graph.evaluate(cypher)
    context = {'integration': total}
    if isinstance(request, dict):
        return render_to_string('dashboard/items/integrationTotal.html',context, request['request'])
    response = {'w':2, 'content': render_to_string('dashboard/items/integrationTotal.html',context, request)}
    return JsonResponse(response)

# 위협 로그 개수
def threatlogTotal(request):
    cypher = '''
    MATCH (threat:Log)-[:DETECTED|FLOW_DETECTED]->(r:Rule)
    RETURN count(threat)
    '''
    total = graph.evaluate(cypher)
    context = {'threat': total}
    if isinstance(request, dict):
        return render_to_string('dashboard/items/threatlogTotal.html',context, request['request'])
    response = {'w':2, 'content': render_to_string('dashboard/items/threatlogTotal.html',context, request)}
    return JsonResponse(response)

# 위협 비율
def threatRatio(request):
    cypher = """
        MATCH (n:Log)
        RETURN COUNT(n)
        """
    log_total = graph.evaluate(cypher)
    cypher = '''
    MATCH (threat:Log)-[:DETECTED|FLOW_DETECTED]->(r:Rule)
    RETURN count(threat)
    '''
    threat_total = graph.evaluate(cypher)
    if log_total == 0:
        threat_ratio = 0
    else:
        threat_ratio = threat_total/log_total
    context = {"threat_ratio": math.ceil(threat_ratio*10)/10}
    if isinstance(request, dict):
        return render_to_string('dashboard/items/threatRatio.html',context, request['request'])
    response = {'w':2, 'content': render_to_string('dashboard/items/threatRatio.html',context, request)}
    return JsonResponse(response)


# 사용자 별 위협 비율
def threatUser(request):
    global graph
    cypher = f"""
    MATCH (r:Rule)<-[:DETECTED|FLOW_DETECTED]-(l:Log)
    WITH count(r) as count,
        CASE
            WHEN l.userIdentity_type = 'Root' THEN l.userIdentity_type
            WHEN l.userIdentity_userName IS NOT NULL THEN l.userIdentity_userName
            ELSE SPLIT(l.userIdentity_arn, '/')[-1]
        END as name
        ORDER BY count DESC
        LIMIT 5
    WHERE name is not null
    WITH count,
        CASE
            WHEN name CONTAINS 'cgid' THEN 'cloudgoat'
            ELSE name
        END as name
    WITH COLLECT(DISTINCT(name)) as name, COLLECT(count) as count
    RETURN name, count
    """
    results = graph.run(cypher)
    user_threat = []
    color = []
    color_list =['#24B6D4','#1cc88a','#f6c23e','#fd7e14','#e74a3b']
    for result in results:
        user_threat = list(result)
    for i, (_) in enumerate(user_threat[0], start=0):
        color.append(color_list[i])
    user_threat = {'name': user_threat[0], 'count': user_threat[1], 'color': color}
    context = {'user_threat': json.dumps(user_threat)}
    if isinstance(request, dict):
        return render_to_string('dashboard/items/threatUser.html',context, request['request'])
    response = {'w':3, 'h':23, 'content': render_to_string('dashboard/items/threatUser.html',context, request)}
    return JsonResponse(response)

# 위협 발생 장비 추이
def threatEquipment(request):
    global graph
    cypher = f"""
    MATCH (r:Rule)<-[:DETECTED|FLOW_DETECTED]-(:Log)
    WITH HEAD([label IN labels(r) WHERE label <> 'Rule']) AS equip
    RETURN equip, count(equip) as count
    """
    results = graph.run(cypher)
    equip_name = []
    equip_count = []
    equip_color = []
    for result in results:
        result = dict(result)
        equip_name.append(result['equip'])
        equip_count.append(result['count'])
        equip_color.append(get_log_color(result['equip']))
    equip_threat = {'name': equip_name, 'count': equip_count, 'color': equip_color}
    context = {'equip_threat': json.dumps(equip_threat)}
    if isinstance(request, dict):
        return render_to_string('dashboard/items/threatEquipment.html',context, request['request'])
    response = {'w':3, 'h':23, 'content': render_to_string('dashboard/items/threatEquipment.html',context, request)}
    return JsonResponse(response)

# 해외 IP 추이
def threatIp(request):
    cypher = f"""
    MATCH (l:Log)
    WHERE l.sourceIPAddress IS NOT NULL AND l.sourceIPAddress =~ '\\d+.\\d+.\\d+.\\d+'
    WITH DISTINCT(l.sourceIPAddress) as ip, COUNT(l.sourceIPAddress) as count
    ORDER BY count DESC LIMIT 5
    RETURN COLLECT(ip) as ip, COLLECT(count) as count
    """
    results = graph.run(cypher)
    ip_country = []
    color = []
    color_list =['#24B6D4','#1cc88a','#f6c23e','#fd7e14','#e74a3b']
    for result in results:
        ip_country = list(result)
    for i, (_) in enumerate(ip_country[0], start=0):
        i %= 5
        color.append(color_list[i])
    ip_country = {'name': ip_country[0], 'count': ip_country[1], 'color': color}
    context = {'ip_country': json.dumps(ip_country)}
    if isinstance(request, dict):
        return render_to_string('dashboard/items/threatIp.html',context, request['request'])
    response = {'w':3, 'h':23, 'content': render_to_string('dashboard/items/threatIp.html',context, request)}
    return JsonResponse(response)

# 정책 별 탐지 위협 개수
def threatRule(request):
    global graph
    cypher = f"""
    MATCH (r:Rule)<-[:DETECTED|FLOW_DETECTED]-(:Log)
    WITH r, HEAD([label IN labels(r) WHERE label <> 'Rule' ]) AS equip
    RETURN equip,
        equip+'_'+r.ruleName as name,
        count(equip) as count
    ORDER BY count DESC
    LIMIT 5
    """
    results = graph.run(cypher)
    name = []
    count = []
    color = []
    for result in results:
        result = dict(result)
        name.append(result['name'])
        count.append(result['count'])
        color.append(get_log_color(result['equip']))
    rule_detected_count = {'name': name, 'count': count, 'color': color}
    context = {'rule_detected_count': json.dumps(rule_detected_count)}
    if isinstance(request, dict):
        return render_to_string('dashboard/items/threatRule.html',context, request['request'])
    response = {'w':3, 'h':23, 'content': render_to_string('dashboard/items/threatRule.html',context, request)}
    return JsonResponse(response)

# 시나리오 분석 위협도
def threatSenario(request):
    global graph
    cypher = f"""
    MATCH (r:Rule)<-[n:DETECTED|FLOW_DETECTED]-(:Log)
    WITH n, r
    WITH count(n) AS rule_count, r.ruleName as name, r.level as level
    WITH level, rule_count,
        CASE
            WHEN rule_count > 50 THEN 4
            WHEN 30 < rule_count <= 50  THEN 3
            WHEN 10 <= rule_count <= 30 THEN 2
            ELSE 1
        END as freq
    WITH freq+level as degree, rule_count
    WITH rule_count,
        CASE
            WHEN 7<= degree <= 8 THEN 4
            WHEN 5<= degree <= 6 THEN 3
            WHEN 3<= degree <= 4 THEN 2
            ELSE 1
        END AS threat_level
    WITH COLLECT({{threat_level: threat_level, rule_count: rule_count}}) as data, sum(rule_count) as num_threat_levels
    UNWIND data as item
    WITH sum((item.threat_level*item.rule_count)) as total_threat_levels, num_threat_levels, data
    UNWIND data as item
    WITH toInteger(round(toFloat(total_threat_levels)/num_threat_levels)) as average, item
    WITH sum(item.rule_count) as count, item.threat_level as level, average
    RETURN average, level, count
    """
    results = graph.run(cypher)
    data =[0,0,0,0]
    average = 1
    for result in results:
        average = result['average'] if 'average' in result else 1
        level = result['level']
        data[level-1] = result['count']
    degree = [3.20, 3.73, 4.25, 4.85]
    color = ['#1cc88a', '#f6c23e', '#fd7e14', '#e74a3b']
    average = {'degree': degree[average-1], 'color': color[average-1]}
    context = {'senario': {'average': json.dumps(average), 'count': (data)}}
    if isinstance(request, dict):
        return render_to_string('dashboard/items/threatSenario.html',context, request['request'])
    response = {'w':2, 'h':23, 'content': render_to_string('dashboard/items/threatSenario.html',context, request)}
    return JsonResponse(response)

# 중요도 별 위협 개수
def threatLevel(request):
    global graph
    cypher = f"""
    MATCH (r:Rule)<-[n:DETECTED|FLOW_DETECTED]-(:Log)
    WITH n, r
    WITH count(n) AS rule_count, r.ruleName as name, r.level as level
    WITH level, rule_count,
        CASE
            WHEN rule_count > 50 THEN 4
            WHEN 30 < rule_count <= 50  THEN 3
            WHEN 10 <= rule_count <= 30 THEN 2
            ELSE 1
        END as freq
    WITH freq+level as degree, rule_count
    WITH rule_count,
        CASE
            WHEN 7<= degree <= 8 THEN 4
            WHEN 5<= degree <= 6 THEN 3
            WHEN 3<= degree <= 4 THEN 2
            ELSE 1
        END AS threat_level
    WITH COLLECT({{threat_level: threat_level, rule_count: rule_count}}) as data, sum(rule_count) as num_threat_levels
    UNWIND data as item
    WITH sum((item.threat_level*item.rule_count)) as total_threat_levels, num_threat_levels, data
    UNWIND data as item
    WITH toInteger(round(toFloat(total_threat_levels)/num_threat_levels)) as average, item
    WITH sum(item.rule_count) as count, item.threat_level as level, average
    RETURN average, level, count
    """
    results = graph.run(cypher)
    data =[0,0,0,0]
    average = 1
    for result in results:
        average = result['average'] if 'average' in result else 1
        level = result['level']
        data[level-1] = result['count']
    degree = [3.20, 3.73, 4.25, 4.85]
    color = ['#1cc88a', '#f6c23e', '#fd7e14', '#e74a3b']
    average = {'degree': degree[average-1], 'color': color[average-1]}
    context = {'senario': {'average': json.dumps(average), 'count': (data)}}
    if isinstance(request, dict):
        return render_to_string('dashboard/items/threatLevel.html',context, request['request'])
    response = {'w':2, 'h':23, 'content': render_to_string('dashboard/items/threatLevel.html',context, request)}
    return JsonResponse(response)

# 최근 수집 로그 Overview
def recentCollectedOverview(request):
    context = get_threat_month('collected')
    if isinstance(request, dict):
        return render_to_string('dashboard/items/recentCollectedOverview.html',context, request['request'])
    response = {'w':4, 'h':27, 'content': render_to_string('dashboard/items/recentCollectedOverview.html',context, request)}
    return JsonResponse(response)

# 위협 로그 Overview
def threatDetectionOverview(request):
    context = get_threat_month('threat')
    if isinstance(request, dict):
        return render_to_string('dashboard/items/threatDetectionOverview.html',context, request['request'])
    response = {'w':4, 'h':27, 'content': render_to_string('dashboard/items/threatDetectionOverview.html',context, request)}
    return JsonResponse(response)

# 최근 수집 및 위협 로그 Overview
def get_threat_month(request):
    month_list = []
    if request == 'collected':
        collected_month = []
    else:
        threat_month = []
    current = datetime.datetime.now()
    cur_month = current.month
    cur_year = current.year
    for i in range(cur_year-1, cur_year+1):
        if i == cur_year-1:
            for j in range(cur_month+3,13):
                month_list.append(str(i)+'/'+str(j))
                if request == 'collected':
                    collected_month.append(get_collected_count(i, j))
                else:
                    threat_month.append(get_threat_count(i, j))
        elif i == cur_year:
            for j in range(1,cur_month+1):
                month_list.append(str(i)+'/'+str(j))
                if request == 'collected':
                    collected_month.append(get_collected_count(i, j))
                else:
                    threat_month.append(get_threat_count(i, j))
        else:
            for j in range(1,13):
                month_list.append(str(i)+'/'+str(j))
                if request == 'collected':
                    collected_month.append(get_collected_count(i, j))
                else:
                    threat_month.append(get_threat_count(i, j))
    if request == 'collected':
        response = {'month': json.dumps(month_list), 'collected_month': json.dumps(collected_month)}
    else:
        response = {'month': json.dumps(month_list), 'threat_month': json.dumps(threat_month)}
    return response

# 위협 로그 Overview
def get_threat_count(year, month):
    start = datetime.datetime(year,month,1,0,0,1).strftime('%Y-%m-%dT%H:%M:%SZ')
    if month == 12:
        end = datetime.datetime(year,month,31,0,0,1).strftime('%Y-%m-%dT%H:%M:%SZ')
    else:
        end = datetime.datetime(year,month+1,1,0,0,1).strftime('%Y-%m-%dT%H:%M:%SZ')
    global graph
    cypher = f"""
        MATCH (n:Log)-[:DETECTED|FLOW_DETECTED]->(r)
        WHERE '{start}'<=n.eventTime<='{end}'
        RETURN count(n)
    """
    response = graph.evaluate(cypher)
    return response

# 최근 수집 로그 Overview
def get_collected_count(year, month):
    start = datetime.datetime(year,month,1,0,0,1).strftime('%Y-%m-%dT%H:%M:%SZ')
    if month == 12:
        end = datetime.datetime(year,month,31,0,0,1).strftime('%Y-%m-%dT%H:%M:%SZ')
    else:
        end = datetime.datetime(year,month+1,1,0,0,1).strftime('%Y-%m-%dT%H:%M:%SZ')
    global graph
    cypher = f"""
        MATCH (n:Log)
        WHERE '{start}'<=n.eventTime<='{end}'
        RETURN count(n)
    """
    response = graph.evaluate(cypher)
    return response


# 최근 탐지 위협 (neo4j graph 연동)
def recentDetection(request):
    cypher = '''
    MATCH (r:Rule)<-[d:DETECTED|FLOW_DETECTED]-(l:Log)
    RETURN
        id(d) AS No,
        head([label IN labels(r) WHERE label <> 'Rule']) AS cloud,
        head([label IN labels(r) WHERE label <> 'Rule'])+'/'+l.sourceIPAddress AS system,
        r.ruleName AS detected_rule,
        r.ruleName+'#'+id(d) AS rule_name,
        l.eventName AS action,
        l.eventTime AS eventTime,
        l.eventTime AS etime,
        r.ruleClass AS rule_class,
        ID(d) as id
    ORDER BY eventTime DESC
    LIMIT 10
    '''
    results = graph.run(cypher)
    data_list = []
    filter = ['cloud', 'detected_rule', 'rule_name', 'eventTime', 'id', 'rule_class']
    for result in results:
        # Change to type dictionary
        data = dict(result.items())
        form_dict = {}
        for key in filter:
            if key != 'detected_rule':
                value = data.pop(key)
            else:
                value = data[key]
            form_dict[key] = value
        data['form'] = form_dict
        data_list.append(data)
    context = {'recent_threat': data_list}
    if isinstance(request, dict):
        return render_to_string('dashboard/items/recentDetection.html',context, request['request'])
    response = {'w':6, 'h':33,'x':5, 'content':render_to_string('dashboard/items/recentDetection.html', context, request)}
    return JsonResponse(response)

# Graph Visual
def graphitem(request):
    if isinstance(request, dict):
        return render_to_string('dashboard/items/graphitem.html',{}, request['request'])
    response = {'w':4, 'h':55, 'content':render_to_string('dashboard/items/graphitem.html', {}, request)}
    return JsonResponse(response)

# CPU 사용량
def cpu(request):
    if isinstance(request, dict):
        return render_to_string('dashboard/items/cpu.html',{}, request['request'])
    response = {'w':2, 'content':render_to_string('dashboard/items/cpu.html',{},request)}
    return JsonResponse(response)

# Memory 사용량
def memory(request):
    if isinstance(request, dict):
        return render_to_string('dashboard/items/memory.html',{}, request['request'])
    response = {'w':2, 'content':render_to_string('dashboard/items/memory.html',{},request)}
    return JsonResponse(response)

# DISK 사용량
def disk(request):
    if isinstance(request, dict):
        return render_to_string('dashboard/items/disk.html',{}, request['request'])
    response = {'w':2, 'content':render_to_string('dashboard/items/disk.html',{},request)}
    return JsonResponse(response)

# Network 사용량
def network(request):
    if isinstance(request, dict):
        return render_to_string('dashboard/items/network.html',{}, request['request'])
    response = {'w':2, 'content':render_to_string('dashboard/items/network.html',{},request)}
    return JsonResponse(response)

# 서버 성능
def get_server_status(request):
    if request.method == 'POST':
        data = request.POST['data']
        response = {}
        if data == 'cpu':
            response['cpu'] = psutil.cpu_percent()
        elif data == 'memory':
            # Memory usage (percentage)
            memory = psutil.virtual_memory()
            response['memory'] = memory.percent
        elif data == 'disk':    
            # Disk usage (percentage)
            disk_partitions = psutil.disk_partitions()
            disk_total_used = 0
            disk_total_available = 0
            for disk_partition in disk_partitions:
                usage = psutil.disk_usage(disk_partition.mountpoint)
                disk_total_used += usage.used
                disk_total_available += usage.total
            disk_total_percent = disk_total_used / disk_total_available * 100
            response['disk'] = disk_total_percent
        elif data == 'network':
            # Network usage (bytes sent and received)
            network = psutil.net_io_counters()
            response['in'] = round(network.bytes_recv/1000, 2)
            response['out'] = round(network.bytes_sent/1000, 2)
        return JsonResponse(json.dumps(response), safe=False)