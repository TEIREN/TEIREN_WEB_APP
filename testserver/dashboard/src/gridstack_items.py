# local
import datetime
import json
import math
import psutil
from common.neo4j.handler import Neo4jHandler

# django
from django.template.loader import render_to_string
from django.shortcuts import render, HttpResponse
from django.http import JsonResponse, HttpResponseRedirect
from django.conf import settings

# 3rd party
from neo4j import GraphDatabase
from py2neo import Graph

# AWS
host = settings.NEO4J['HOST']
port = settings.NEO4J["PORT"]
username = settings.NEO4J['USERNAME']
password = settings.NEO4J['PASSWORD']
graph = Graph(f"bolt://{host}:{port}", auth=(username, password))

color = {
    "Aws" : "#FF9900",
    "NCP" : "#1EC800",
    "NHN" : "#4E73DF",
    "Teiren": "#6FADCF",
    "OFFICEKEEPER" : "#0059A9",
    "WINDOWS_EVENT_LOG" : "#357EC7"
}

# 로그 Bar Chart Color 지정
def get_log_color(collection_name):
    color = {
        "Aws" : "#FF9900",
        "NCP" : "#1EC800",
        "NHN" : "#4E73DF",
        "OFFICEKEEPER" : "#0059A9",
        "WINDOWS_EVENT_LOG" : "#357EC7"
    }
    
    return color[collection_name] if collection_name in color else '#24B6D4'

class DashboardHandler(Neo4jHandler):
    def __init__(self, request) -> None:
        """This class receives 2 types of requsts 

        Args:
            request (dict): {'request': <reqeust>}
            request (session): <request>
        """
        super().__init__()
        self.request = request
        self.user_db = self.request.get('request').session.get('db_name')
    
    def logTotal(self):
        query = """
        MATCH (n:Log)
        RETURN COUNT(n) AS count
        """
        log_total = self.run(self.user_db, query)
        context = {"total": f"{log_total['count']:,}"}
        if isinstance(self.request, dict):
            return render_to_string('dashboard/items/logTotal.html',context, self.request['request'])
        
        response = {'w':2, 'h':8, 'content': render_to_string('dashboard/items/logTotal.html',context, self.request)}
        return JsonResponse(response)

    def integrationTotal(self):
        cypher = f"""
        MATCH (i:Integration)
        RETURN count(i) AS count
        """
        total = self.run(self.user_db, cypher)
        context = {'integration': total['count']}
        if isinstance(self.request, dict):
            return render_to_string('dashboard/items/integrationTotal.html',context, self.request['request'])
        response = {'w':2, 'h':8, 'content': render_to_string('dashboard/items/integrationTotal.html',context, self.request)}
        
        return JsonResponse(response)
    
    def threatlogTotal(self):
        cypher = '''
        MATCH (threat:Log)-[:DETECTED|FLOW_DETECTED]->(r:Rule)
        RETURN count(threat) AS count
        '''
        total = self.run(self.user_db, cypher)
        context = {'threat': total['count']}
        
        if isinstance(self.request, dict):
            return render_to_string('dashboard/items/threatlogTotal.html',context, self.request['request'])
        response = {'w':2, 'h':8, 'content': render_to_string('dashboard/items/threatlogTotal.html',context, self.request)}
        
        return JsonResponse(response)

    # 위협 비율
    def threatRatio(self):
        cypher = """
            MATCH (n:Log)
            RETURN COUNT(n) AS count
            """
        log_total = self.run(self.user_db, cypher)
        cypher = '''
        MATCH (threat:Log)-[:DETECTED|FLOW_DETECTED]->(r:Rule)
        RETURN count(threat) AS count
        '''
        threat_total = self.run(self.user_db, cypher)
        threat_ratio = 0 if log_total['count'] == 0 else threat_total['count']/log_total['count']
        context = {"threat_ratio": math.ceil(threat_ratio*10)/10}
        if isinstance(self.request, dict):
            return render_to_string('dashboard/items/threatRatio.html',context, self.request['request'])
        response = {'w':2, 'h':8, 'content': render_to_string('dashboard/items/threatRatio.html',context, self.request)}
        
        return JsonResponse(response)
    
    # 사용자 별 위협 비율
    def threatUser(self):
        cypher = f"""
        MATCH (r:Rule)<-[:DETECTED|FLOW_DETECTED]-(l:Log)
        WITH count(r) as count,
            CASE
                WHEN l.userIdentity_type = 'Root' THEN l.userIdentity_type
                WHEN l.userIdentity_userName IS NOT NULL THEN l.userIdentity_userName
                WHEN l.userName IS NOT NULL THEN l.userName
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
        WITH COLLECT(DISTINCT(name)) as names, COLLECT(count) as counts
        RETURN names AS names, counts AS counts
        """
        results = self.run(database=self.user_db, query=cypher)
        user_threat = {'name': results['names'], 'count': results['counts'], 'color': ['#24B6D4','#1cc88a','#f6c23e','#fd7e14','#e74a3b']}
        context = {'user_threat': json.dumps(user_threat)}
        if isinstance(self.request, dict):
            return render_to_string('dashboard/items/threatUser.html',context, self.request['request'])
        response = {'w':3, 'h':23, 'content': render_to_string('dashboard/items/threatUser.html',context, self.request)}
        return JsonResponse(response)

    # 위협 발생 장비 추이
    def threatEquipment(self):
        cypher = f"""
        MATCH (r:Rule)<-[:DETECTED|FLOW_DETECTED]-(:Log)
        WITH HEAD([label IN labels(r) WHERE label <> 'Rule']) AS equip
        WITH equip as equip, count(equip) as count
        RETURN COLLECT(equip) as equip, COLLECT(count) as count
        """
        results = self.run(self.user_db, cypher)
        # equip_color = [color.get(result['equip']) for result in results]
        if results['equip'] and results['count']:
            print(results)
            equip_threat = {
                'name': results['equip'],
                'count': results['count'],
                'color': [color.get(resource) for resource in results['equip']]
            }
        else:
            equip_threat = {
                'name': ['None',],
                'count': ['0',],
                'color': ['#FF9900']
            }
        context = {'equip_threat': json.dumps(equip_threat)}
        if isinstance(self.request, dict):
            return render_to_string('dashboard/items/threatEquipment.html',context, self.request['request'])
        response = {'w':3, 'h':23, 'content': render_to_string('dashboard/items/threatEquipment.html',context, self.request)}
        return JsonResponse(response)

    # 해외 IP 추이
    def threatIp(self):
        cypher = f"""
        MATCH (l:Log)
        WHERE l.sourceIPAddress IS NOT NULL AND l.sourceIPAddress =~ '\\d+.\\d+.\\d+.\\d+'
        WITH DISTINCT(l.sourceIPAddress) as ip, COUNT(l.sourceIPAddress) as count
        ORDER BY count DESC LIMIT 5
        RETURN COLLECT(ip) as ips, COLLECT(count) as counts
        """
        results = self.run(self.user_db, cypher)
        ip_country = {'name': results['ips'], 
                      'count': results['counts'],
                      'color': ['#24B6D4','#1cc88a','#f6c23e','#fd7e14','#e74a3b']}
        context = {'ip_country': json.dumps(ip_country)}
        if isinstance(self.request, dict):
            return render_to_string('dashboard/items/threatIp.html',context, self.request['request'])
        response = {'w':3, 'h':23, 'content': render_to_string('dashboard/items/threatIp.html',context, self.request)}
        return JsonResponse(response)

    # 정책 별 탐지 위협 개수
    def threatRule(self):
        cypher = f"""
        MATCH (r:Rule)<-[:DETECTED|FLOW_DETECTED]-(:Log)
        WITH r, HEAD([label IN labels(r) WHERE label <> 'Rule' ]) AS equip
        WITH equip, equip+'_'+r.ruleName as name, count(equip) as count
        ORDER BY count DESC
        LIMIT 5
        RETURN COLLECT(equip) as equip, COLLECT(name) as name, COLLECT(count) as count
        """
        results = self.run(self.user_db, cypher)
        equip_color = [color.get(equip) for equip in results['equip']]
        rule_detected_count = {'name': results['name'], 'count': results['count'], 'color': equip_color}
        context = {'rule_detected_count': json.dumps(rule_detected_count)}
        if isinstance(self.request, dict):
            return render_to_string('dashboard/items/threatRule.html',context, self.request['request'])
        response = {'w':3, 'h':23, 'content': render_to_string('dashboard/items/threatRule.html',context, self.request)}
        return JsonResponse(response)

    # 시나리오 분석 위협도
    def threatSenario(self):
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
        return  COLLECT(average) as average, COLLECT(level) as level, COLLECT(count) as count
        """
        results = self.run(self.user_db, cypher)
        degree = {
            1: 3.20,
            2: 3.73,
            3: 4.25,
            4: 4.85,
        }
        color = {
            1: '#1cc88a',
            2: '#f6c23e', 
            3: '#fd7e14',
            4: '#e74a3b',
        }
        average = results['average'][0] if results['average'] and results['average'][0] else 1 # True Value
        average_data = {'degree': degree.get(average), 'color': color.get(average)}
        context = {
            'senario': {
                'average': json.dumps(average_data), 
                'count': results['count']
            }
        }
        if isinstance(self.request, dict):
            return render_to_string('dashboard/items/threatSenario.html',context, self.request['request'])
        response = {'w':2, 'h':23, 'content': render_to_string('dashboard/items/threatSenario.html',context, self.request)}
        return JsonResponse(response)

    # 중요도 별 위협 개수
    def threatLevel(self):
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
        return  COLLECT(average) as average, COLLECT(level) as level, COLLECT(count) as count
        """
        results = self.run(self.user_db, cypher)
        degree = {
            1: 3.20,
            2: 3.73,
            3: 4.25,
            4: 4.85,
        }
        color = {
            1: '#1cc88a',
            2: '#f6c23e', 
            3: '#fd7e14',
            4: '#e74a3b',
        }
        average = results['average'][0] if results['average'] and results['average'][0] else 1 # True Value
        average_data = {'degree': degree.get(average), 'color': color.get(average)}
        count_list = results['count']
        count_list.extend([0] * (4 - len(count_list)))
        context = {
            'senario': {
                'average': json.dumps(average_data),
                'count': count_list
            }
        }
        
        if isinstance(self.request, dict):
            return render_to_string('dashboard/items/threatLevel.html',context, self.request['request'])
        response = {'w':2, 'h':23, 'content': render_to_string('dashboard/items/threatLevel.html',context, self.request)}
        return JsonResponse(response)

    # 최근 수집 로그 Overview
    def recentCollectedOverview(self):
        context = self.get_threat_month('collected')
        if isinstance(self.request, dict):
            return render_to_string('dashboard/items/recentCollectedOverview.html',context, self.request['request'])
        response = {'w':4, 'h':27, 'content': render_to_string('dashboard/items/recentCollectedOverview.html',context, self.request)}
        return JsonResponse(response)

    # 위협 로그 Overview
    def threatDetectionOverview(self):
        context = self.get_threat_month('threat')
        if isinstance(self.request, dict):
            return render_to_string('dashboard/items/threatDetectionOverview.html',context, self.request['request'])
        response = {'w':4, 'h':27, 'content': render_to_string('dashboard/items/threatDetectionOverview.html',context, self.request)}
        return JsonResponse(response)

    # 최근 탐지 위협 (neo4j graph 연동)
    def recentDetection(self):
        cypher = '''
        MATCH (r:Rule)<-[d:DETECTED|FLOW_DETECTED]-(l:Log)
        WITH
            d.alert as alert,
            id(d) AS No,
            CASE
                WHEN r.level = 1 THEN 'success' 
                WHEN r.level = 2 THEN 'warning'
                WHEN r.level = 3 THEN 'caution'
                ELSE 'danger'
            END AS level,
            head([label IN labels(r) WHERE label <> 'Rule']) AS resource,
            CASE
                WHEN l.sourceIPAddress IS NOT NULL THEN head([label IN labels(r) WHERE label <> 'Rule'])+'/'+l.sourceIPAddress
                WHEN l.sourceIp IS NOT NULL THEN head([label IN labels(r) WHERE label <> 'Rule'])+'/'+l.sourceIp
                ELSE head([label IN labels(r) WHERE label <> 'Rule'])+'/-'
            END AS system,
            r.ruleName AS detected_rule,
            r.ruleName+'#'+id(d) AS rule_name,
            l.eventName AS action,
            l.eventTime AS eventTime,
            l.eventTime AS etime,
            r.ruleClass AS rule_class,
            ID(d) as id
        ORDER BY eventTime DESC LIMIT 10
        RETURN
            COLLECT(alert) AS alert,
            COLLECT(No) AS No,
            COLLECT(level) AS level,
            COLLECT(resource) AS resource,
            COLLECT(system) AS system,
            COLLECT(detected_rule) AS detected_rule,
            COLLECT(rule_name) AS rule_name,
            COLLECT(action) AS action,
            COLLECT(eventTime) AS eventTime,
            COLLECT(etime) AS etime,
            COLLECT(rule_class) AS rule_class,
            COLLECT(id) AS id
        '''
        results = self.run(self.user_db, cypher)
        if not results['id']:
            context = {
                'alert': None,
                'No': None,
                'level': None,
                'system': None,
                'rule_name': None,
                'action': None,
                'etime': None,
                'form': {
                    'resource': None,
                    'detected_rule': None,
                    'rule_name': None,
                    'eventTime': None,
                    'id': None,
                    'rule_class': None,
                }
            }
            return render_to_string('dashboard/items/recentDetection.html',context, self.request['request'])
        
        form_data = []
        for index in range(len(results[0])):
            context = {
                'alert': results['alert'][index],
                'No': results['No'][index],
                'level': results['level'][index],
                'system': results['system'][index],
                'rule_name': results['rule_name'][index],
                'action': results['action'][index],
                'etime': results['etime'][index],
                'form': {
                    'resource': results['resource'][index],
                    'detected_rule': results['detected_rule'][index],
                    'rule_name': results['rule_name'][index],
                    'eventTime': results['eventTime'][index],
                    'id': results['id'][index],
                    'rule_class': results['rule_class'][index],
                }
            }
            print(context)
            print('*'*100)
            form_data.append(context)
        context = {'recent_threat': form_data}
        if isinstance(self.request, dict):
            return render_to_string('dashboard/items/recentDetection.html',context, self.request['request'])
        response = {'w':8, 'h':33, 'x':5, 'content':render_to_string('dashboard/items/recentDetection.html', context, self.request)}
        return JsonResponse(response)
    
    # 최근 수집 및 위협 로그 Overview
    def get_threat_month(self, threat_type):
        if threat_type == 'collected':
            collected_month = []
        if threat_type == 'threat':
            threat_month = []
            
        month_list = []
        current = datetime.datetime.now()
        cur_month = current.month
        cur_year = current.year
        for i in range(cur_year-1, cur_year+1):
            if i == cur_year-1:
                for j in range(cur_month+3,13):
                    month_list.append(str(i)+'/'+str(j))
                    if threat_type == 'collected':
                        collected_month.append(self.get_collected_count(i, j))
                    if threat_type == 'threat':
                        threat_month.append(self.get_threat_count(i, j))
            elif i == cur_year:
                for j in range(1,cur_month+1):
                    month_list.append(str(i)+'/'+str(j))
                    if threat_type == 'collected':
                        collected_month.append(self.get_collected_count(i, j))
                    if threat_type == 'threat':
                        threat_month.append(self.get_threat_count(i, j))
            else:
                for j in range(1,13):
                    month_list.append(str(i)+'/'+str(j))
                    if threat_type == 'collected':
                        collected_month.append(self.get_collected_count(i, j))
                    if threat_type == 'threat':
                        threat_month.append(self.get_threat_count(i, j))
                        
        if threat_type == 'collected':
            response = {'month': json.dumps(month_list), 'collected_month': json.dumps(collected_month)}
        if threat_type == 'threat':
            response = {'month': json.dumps(month_list), 'threat_month': json.dumps(threat_month)}
        
        return response

    # 위협 로그 Overview
    def get_threat_count(self, year, month):
        start = datetime.datetime(year,month,1,0,0,1).strftime('%Y-%m-%dT%H:%M:%SZ')
        if month == 12:
            end = datetime.datetime(year,month,31,0,0,1).strftime('%Y-%m-%dT%H:%M:%SZ')
        else:
            end = datetime.datetime(year,month+1,1,0,0,1).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        cypher = f"""
            MATCH (n:Log)-[:DETECTED|FLOW_DETECTED]->(r)
            WHERE '{start}'<=n.eventTime<='{end}'
            RETURN count(n) AS count
        """
        response = self.run(self.user_db, cypher)
        return response['count']

    # 최근 수집 로그 Overview
    def get_collected_count(self, year, month):
        start = datetime.datetime(year,month,1,0,0,1).strftime('%Y-%m-%dT%H:%M:%SZ')
        if month == 12:
            end = datetime.datetime(year,month,31,0,0,1).strftime('%Y-%m-%dT%H:%M:%SZ')
        else:
            end = datetime.datetime(year,month+1,1,0,0,1).strftime('%Y-%m-%dT%H:%M:%SZ')
        cypher = f"""
            MATCH (n:Log)
            WHERE '{start}'<=n.eventTime<='{end}'
            RETURN count(n) AS count
        """
        response = self.run(self.user_db, cypher)
        return response['count']

    # Graph Visual
    def graphitem(self):
        print('graphitem')
        if isinstance(self.request, dict):
            return render_to_string('dashboard/items/graphitem.html',{}, self.request['request'])
        print('222')
        response = {'w':4, 'h':56, 'x':0,'content':render_to_string('dashboard/items/graphitem.html', {}, self.request)}
        return JsonResponse(response)

    # CPU 사용량
    def cpu(self):
        if isinstance(self.request, dict):
            return render_to_string('dashboard/items/cpu.html',{}, self.request['request'])
        response = {'w':2, 'h':23, 'content':render_to_string('dashboard/items/cpu.html',{}, self.request)}
        return JsonResponse(response)

    # Memory 사용량
    def memory(self):
        if isinstance(self.request, dict):
            return render_to_string('dashboard/items/memory.html',{}, self.request['request'])
        response = {'w':2, 'h':23, 'content':render_to_string('dashboard/items/memory.html',{}, self.request)}
        return JsonResponse(response)

    # DISK 사용량
    def disk(self):
        if isinstance(self.request, dict):
            return render_to_string('dashboard/items/disk.html',{}, self.request['request'])
        response = {'w':2, 'h':23, 'content':render_to_string('dashboard/items/disk.html',{}, self.request)}
        return JsonResponse(response)

    # Network 사용량
    def network(self):
        if isinstance(self.request, dict):
            return render_to_string('dashboard/items/network.html',{}, self.request['request'])
        response = {'w':2, 'h':23, 'content':render_to_string('dashboard/items/network.html',{}, self.request)}
        return JsonResponse(response)

    # 서버 성능
    def get_server_status(self):
        if self.request.method == 'POST':
            data = self.request.POST['data']
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


# 로그 총 개수
def logTotal(request):
    query = """
    MATCH (n:Log)
    RETURN COUNT(n) AS total
    """
    user_db = request.GET.get('uuid')
    with Neo4jHandler as neohandler:
        log_total = neohandler.run(GraphDatabase.user_db, query=query)
    
    context = {"total": format(log_total, ",")}
    if isinstance(request, dict):
        return render_to_string('dashboard/items/logTotal.html',context, request)
    
    response = {'w':2, 'h':8, 'content': render_to_string('dashboard/items/logTotal.html',context, request)}
    
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
        return render_to_string('dashboard/items/integrationTotal.html',context, request)
    response = {'w':2, 'h':8, 'content': render_to_string('dashboard/items/integrationTotal.html',context, request)}
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
        return render_to_string('dashboard/items/threatlogTotal.html',context, request)
    response = {'w':2, 'h':8, 'content': render_to_string('dashboard/items/threatlogTotal.html',context, request)}
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
        return render_to_string('dashboard/items/threatRatio.html',context, request)
    response = {'w':2, 'h':8, 'content': render_to_string('dashboard/items/threatRatio.html',context, request)}
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
            WHEN l.userName IS NOT NULL THEN l.userName
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
        return render_to_string('dashboard/items/threatUser.html',context, request)
    response = {'w':3, 'h':23, 'content': render_to_string('dashboard/items/threatUser.html',context, request)}
    return JsonResponse(response)

# 위협 발생 장비 추이
# RESORUCE OVERVIEW
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
        return render_to_string('dashboard/items/threatEquipment.html',context, request)
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
        return render_to_string('dashboard/items/threatIp.html',context, request)
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
        return render_to_string('dashboard/items/threatRule.html',context, request)
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
        average = result['average'] if result['average'] else 1
        level = result['level']
        data[level-1] = result['count']
    degree = [3.20, 3.73, 4.25, 4.85]
    color = ['#1cc88a', '#f6c23e', '#fd7e14', '#e74a3b']
    average = {'degree': degree[average-1], 'color': color[average-1]}
    context = {'senario': {'average': json.dumps(average), 'count': (data)}}
    if isinstance(request, dict):
        return render_to_string('dashboard/items/threatSenario.html',context, request)
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
        average = result['average'] if result['average'] else 1
        level = result['level']
        data[level-1] = result['count']
    degree = [3.20, 3.73, 4.25, 4.85]
    color = ['#1cc88a', '#f6c23e', '#fd7e14', '#e74a3b']
    average = {'degree': degree[average-1], 'color': color[average-1]}
    context = {'senario': {'average': json.dumps(average), 'count': (data)}}
    if isinstance(request, dict):
        return render_to_string('dashboard/items/threatLevel.html',context, request)
    response = {'w':2, 'h':23, 'content': render_to_string('dashboard/items/threatLevel.html',context, request)}
    return JsonResponse(response)

# 최근 수집 로그 Overview
def recentCollectedOverview(request):
    context = get_threat_month('collected')
    if isinstance(request, dict):
        return render_to_string('dashboard/items/recentCollectedOverview.html',context, request)
    response = {'w':4, 'h':27, 'content': render_to_string('dashboard/items/recentCollectedOverview.html',context, request)}
    return JsonResponse(response)

# 위협 로그 Overview
def threatDetectionOverview(request):
    context = get_threat_month('threat')
    if isinstance(request, dict):
        return render_to_string('dashboard/items/threatDetectionOverview.html',context, request)
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
        d.alert as alert,
        id(d) AS No,
        CASE
            WHEN r.level = 1 THEN 'success' 
            WHEN r.level = 2 THEN 'warning'
            WHEN r.level = 3 THEN 'caution'
            ELSE 'danger'
        END AS level,
        head([label IN labels(r) WHERE label <> 'Rule']) AS logType,
        CASE
            WHEN l.sourceIPAddress IS NOT NULL THEN head([label IN labels(r) WHERE label <> 'Rule'])+'/'+l.sourceIPAddress
            WHEN l.sourceIp IS NOT NULL THEN head([label IN labels(r) WHERE label <> 'Rule'])+'/'+l.sourceIp
            ELSE head([label IN labels(r) WHERE label <> 'Rule'])+'/-'
        END AS system,
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
    filter = ['logType', 'detected_rule', 'rule_name', 'eventTime', 'id', 'rule_class']
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
        return render_to_string('dashboard/items/recentDetection.html',context, request)
    response = {'w':8, 'h':33, 'x':5, 'content':render_to_string('dashboard/items/recentDetection.html', context, request)}
    return JsonResponse(response)

# Graph Visual
def graphitem(request):
    if isinstance(request, dict):
        return render_to_string('dashboard/items/graphitem.html',{}, request)
    response = {'w':4, 'h':56, 'x':0,'content':render_to_string('dashboard/items/graphitem.html', {}, request)}
    return JsonResponse(response)

# CPU 사용량
def cpu(request):
    if isinstance(request, dict):
        return render_to_string('dashboard/items/cpu.html',{}, request)
    response = {'w':2, 'h':23, 'content':render_to_string('dashboard/items/cpu.html',{},request)}
    return JsonResponse(response)

# Memory 사용량
def memory(request):
    if isinstance(request, dict):
        return render_to_string('dashboard/items/memory.html',{}, request)
    response = {'w':2, 'h':23, 'content':render_to_string('dashboard/items/memory.html',{},request)}
    return JsonResponse(response)

# DISK 사용량
def disk(request):
    if isinstance(request, dict):
        return render_to_string('dashboard/items/disk.html',{}, request)
    response = {'w':2, 'h':23, 'content':render_to_string('dashboard/items/disk.html',{},request)}
    return JsonResponse(response)

# Network 사용량
def network(request):
    if isinstance(request, dict):
        return render_to_string('dashboard/items/network.html',{}, request)
    response = {'w':2, 'h':23, 'content':render_to_string('dashboard/items/network.html',{},request)}
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