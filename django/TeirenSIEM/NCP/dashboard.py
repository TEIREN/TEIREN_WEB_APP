# from django.http import JsonResponse
# from pymongo import MongoClient
# from py2neo import Graph
# from django.conf import settings
# import datetime
# import json
# import time
# import psutil
# import random

# client = MongoClient (
#     host = settings.MONGODB['HOST'],
#     port = settings.MONGODB['PORT'],
#     username = settings.MONGODB['USERNAME'],
#     password = settings.MONGODB['PASSWORD']
# )

# graph = Graph(f"bolt://{settings.NEO4J_HOST}:{settings.NEO4J_PORT}", auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD))

# def dashboard_chart():
#     response = aws.dashboard.get_recent_threat()
#     response.update(aws.dashboard.get_threat_month())
#     response.update(aws.dashboard.get_equip_threat())
#     response.update(aws.dashboard.get_rule_detected_count())
#     response.update(aws.dashboard.get_user_threat())
#     response.update(get_ip_country())
#     response.update(aws.dashboard.get_senario_threat())
#     return response

# # Mongo DB filtering list_collection_names()
# def filter_collection_names(collections):
#     prefixes = ['auth_','django_','__','mapping']
#     collections = [name for name in collections if not any(name.startswith(prefix) for prefix in prefixes)]
#     return collections

# # Random Hex Color Code
# def random_hex_color():
#     color = '#' + ''.join([random.choice('0123456789ABCDEF') for _ in range(6)])
#     return color
    
# # 로그 Bar Chart Color 지정
# def get_log_color(collection_name):
#     response = ''
#     color = {
#         "AWS" : "#FF9900",
#         "NCP" : "#1EC800",
#         "NHN" : "#4E73DF",
#         "OFFICEKEEPER" : "#0059A9",
#         "WINDOWS_EVENT_LOG" : "#357EC7"
#     }
#     if collection_name in color:
#         response = color[collection_name]
#     else:
#         return False
#     return response

# # 로그 총 개수
# def get_log_total():
#     global client
#     db = client['ts_db']
#     collections = db.list_collection_names()
#     collections = filter_collection_names(collections)
#     response= []
#     total = 0
#     log_data = {}
#     for collection_name in collections:
#         collection = db[collection_name]
#         count = collection.count()
#         data = {
#             str(collection_name) : {
#                 "count": count,
#                 "color": get_log_color(collection_name)
#             }
#         }
#         total += count
#         log_data.update(data)
#     log_data = dict(sorted(log_data.items(), key=lambda x: x[1]["count"], reverse=True))
#     response = [total, {'log_data': json.dumps(log_data)}]
#     return response

# # 연동된 제품 개수
# def get_integration_total():
#     global client
#     db = client['ts_config']
#     collection = db['config']
#     filter = {"EMAIL_AGENT": {"$exists":False}}
#     total = format(collection.count(filter), ",")
#     return total

# # 위협 총 개수
# def get_threat_total():
#     global graph
#     cypher ='''
#         MATCH (threat:LOG)-[:DETECTED|FLOW_DETECTED]->(r:RULE)
#         WHERE r.is_allow = 1
#         RETURN count(threat)
#         '''
#     total = graph.evaluate(cypher)
#     return total

# # 서비스 위협 로그 개수
# def get_threat_type_count(collection, key, property):
#     global graph
#     cypher = f'''
#         MATCH (threat:LOG:{collection})-[:DETECTED|FLOW_DETECTED]-(r)
#         WHERE threat.{property} = '{key}'
#             AND r.is_allow = 1
#         RETURN count(threat)
#         '''
#     count = graph.evaluate(cypher)
#     return count

# # 각 제품 내 서비스
# def get_threat_types():
#     global client
#     db = client['ts_db']
#     collections = db.list_collection_names()
#     collections = filter_collection_names(collections)
#     response = {}
#     total = 0
#     for collection_name in collections:
#         collection = db[collection_name]
#         response[collection_name] = {}
#         if collection_name == 'NCP':
#             key_name = 'productName'
#             distinct_keys = collection.distinct(key_name)
#         elif collection_name == 'AWS':
#             key_name = 'eventSource'
#             distinct_keys = collection.distinct(key_name)
#             for i in range(len(distinct_keys)):
#                 distinct_keys[i] = distinct_keys[i].split('.')[0]
#         elif collection_name == 'NHN':
#             key_name = 'eventId'
#             distinct_keys = collection.distinct(key_name)
#             for i in range(len(distinct_keys)):
#                 distinct_keys[i] = distinct_keys[i].split('.')[1]
#         else:
#             continue
#         type_total = 0
#         for key in distinct_keys:
#             val = get_threat_type_count(collection_name, key, key_name)
#             response[collection_name][key.upper()] = val
#             type_total += val
#         response[collection_name] = dict(sorted(response[collection_name].items(), key=lambda x: x[1], reverse=True))
#         response[collection_name]['total'] = type_total
#     return response

# # 최근 수집 및 위협 로그 Overview
# def get_threat_month():
#     month_list = []
#     threat_month = []
#     collected_month = []
#     current = datetime.datetime.now()
#     cur_month = current.month
#     cur_year = current.year
#     for i in range(2022, cur_year+1):
#         if i == 2022:
#             for j in range(8,13):
#                 month_list.append(str(i)+'/'+str(j))
#                 threat_month.append(get_threat_count(i, j))
#                 collected_month.append(get_collected_count(i, j))
#         elif i == cur_year:
#             for j in range(1,cur_month+1):
#                 month_list.append(str(i)+'/'+str(j))
#                 threat_month.append(get_threat_count(i, j))
#                 collected_month.append(get_collected_count(i, j))
#         else:
#             for j in range(1,13):
#                 month_list.append(str(i)+'/'+str(j))
#                 threat_month.append(get_threat_count(i, j))
#                 collected_month.append(get_collected_count(i, j))
#     response = {'month': json.dumps(month_list), 'threat_month': json.dumps(threat_month), 'collected_month': json.dumps(collected_month)}
#     return response

# ## 위협 로그 Overview
# def get_threat_count(year, month):
#     start = datetime.datetime(year, month,1)
#     start = int(time.mktime(start.timetuple()))*1000
#     if month == 12:
#         end = datetime.datetime(year, month, 31)
#     else:
#         end = datetime.datetime(year, month+1, 1)
#     end = int(time.mktime(end.timetuple()))*1000
#     global graph
#     cypher = f"""
#         MATCH (x)-[:DETECTED|FLOW_DETECTED]->(r)
#         WHERE r.is_allow = 1 and {start}<=x.eventTime<={end}
#         RETURN count(x)
#     """
#     results = graph.run(cypher)
#     for result in results:
#         response = result['count(x)']
#     return response

# ## 최근 수집 로그 Overview
# def get_collected_count(year, month):
#     start = datetime.datetime(year, month,1)
#     start = int(time.mktime(start.timetuple()))*1000
#     if month == 12:
#         end = datetime.datetime(year, month, 31)
#     else:
#         end = datetime.datetime(year, month+1, 1)
#     end = int(time.mktime(end.timetuple()))*1000
#     global graph
#     cypher = f"""
#         MATCH (x:LOG)
#         WHERE {start}<=x.eventTime<={end}
#         RETURN count(x)
#     """
#     results = graph.run(cypher)
#     for result in results:
#         response = result['count(x)']
#     return response

# # 서버 성능
# def get_server_status(request):
#     if request.method == 'POST':
#         data = request.POST['data']
#         response = {}
#         if data == 'cpu':
#             response['cpu'] = psutil.cpu_percent()
#         elif data == 'memory':
#             # Memory usage (percentage)
#             memory = psutil.virtual_memory()
#             response['memory'] = memory.percent
#         elif data == 'disk':    
#             # Disk usage (percentage)
#             disk_partitions = psutil.disk_partitions()
#             disk_total_used = 0
#             disk_total_available = 0
#             for disk_partition in disk_partitions:
#                 usage = psutil.disk_usage(disk_partition.mountpoint)
#                 disk_total_used += usage.used
#                 disk_total_available += usage.total
#             disk_total_percent = disk_total_used / disk_total_available * 100
#             response['disk'] = disk_total_percent
#         elif data == 'network':
#             # Network usage (bytes sent and received)
#             network = psutil.net_io_counters()
#             response['in'] = round(network.bytes_recv/1000, 2)
#             response['out'] = round(network.bytes_sent/1000, 2)
#         return JsonResponse(json.dumps(response), safe=False)

# ## 위협 발생 장비 추이
# def get_equip_threat():
#     global graph
#     cypher = f"""
#     MATCH (n:RULE)<-[:DETECTED|FLOW_DETECTED]-()
#     WHERE n.is_allow = 1
#     WITH 
#         HEAD([label IN labels(n) WHERE label <> 'RULE' AND label <> 'FLOW']) AS equip
#     RETURN
#         equip,
#         count(equip) as count
#     """
#     results = graph.run(cypher)
#     equip_name = []
#     equip_count = []
#     equip_color = []
#     for result in results:
#         result = dict(result)
#         equip_name.append(result['equip'])
#         equip_count.append(result['count'])
#         equip_color.append(get_log_color(result['equip']))
#     equip_threat = {'name': equip_name, 'count': equip_count, 'color': equip_color}
#     response = {'equip_threat': json.dumps(equip_threat)}
#     return response

# ## 정책 별 탐지 위협 개수
# def get_rule_detected_count():
#     global graph
#     cypher = f"""
#     MATCH (n:RULE)<-[:DETECTED|FLOW_DETECTED]-()
#     WHERE n.is_allow = 1
#     WITH
#         n,
#         HEAD([label IN labels(n) WHERE label <> 'RULE' AND label <> 'FLOW']) AS equip
#     RETURN
#         equip,
#         equip+'_'+n.name as name,
#         count(equip) as count
#     ORDER BY count DESC
#     LIMIT 5
#     """
#     results = graph.run(cypher)
#     name = []
#     count = []
#     color = []
#     for result in results:
#         result = dict(result)
#         name.append(result['name'])
#         count.append(result['count'])
#         color.append(get_log_color(result['equip']))
#     rule_detected_count = {'name': name, 'count': count, 'color': color}
#     response = {'rule_detected_count': json.dumps(rule_detected_count)}
#     return response

# ## 사용자 별 위협 비율
# def get_user_threat():
#     global graph
#     cypher = f"""
#     MATCH (n:RULE)<-[*]-(a:ACCOUNT)
#     WHERE n.is_allow = 1
#     WITH
#         a.userName as name,
#         count(n) as count
#     ORDER BY count DESC
#     LIMIT 5
#     WITH 
#         COLLECT(name) as name,
#         COLLECT(count) as count
#     RETURN name, count
#     """
#     results = graph.run(cypher)
#     user_threat = []
#     color = []
#     color_list =['#24B6D4','#1cc88a','#f6c23e','#fd7e14','#e74a3b']
#     for result in results:
#         user_threat = list(result)
#     for i, (_) in enumerate(user_threat[0], start=0):
#         color.append(color_list[i])
#     user_threat = {'name': user_threat[0], 'count': user_threat[1], 'color': color}
#     response = {'user_threat': json.dumps(user_threat)}
#     return response

# ## 해외 ip 접근 추이
# def get_ip_country():
#     global graph
#     cypher = f"""
#     MATCH (n:LOG)
#     WHERE 
#         n.sourceIp IS NOT NULL AND
#         n.clientIpCountry IS NOT NULL AND
#         n.clientIpCountry <> 'KR'
#     WITH
#         DISTINCT n.clientIpCountry as country, 
#         count(n.clientIpCountry) as count
#     RETURN
#         COLLECT(country) as country,
#         COLLECT(count) as count
#     """
#     results = graph.run(cypher)
#     ip_country = []
#     color = []
#     color_list =['#24B6D4','#1cc88a','#f6c23e','#fd7e14','#e74a3b']
#     for result in results:
#         ip_country = list(result)
#     for i, (_) in enumerate(ip_country[0], start=0):
#         i %= 5
#         color.append(color_list[i])
#     ip_country = {'name': ip_country[0], 'count': ip_country[1], 'color': color}
#     response = {'ip_country': json.dumps(ip_country)}
#     return response

# ## 시나리오 분석 위협도, 중요도 별 위협 개수
# def get_senario_threat():
#     global graph
#     cypher = f"""
#     MATCH (r:RULE)<-[n:DETECTED|FLOW_DETECTED]-()
#     WHERE r.is_allow = 1
#     WITH date(datetime({{epochMillis:n.detected_time}})) AS time, n, r
#     WITH count(n) AS rule_count, n.name as name, r.level as level
#     WITH level, rule_count,
#         CASE
#             WHEN rule_count > 50 THEN 4
#             WHEN 30 < rule_count <= 50  THEN 3
#             WHEN 10 <= rule_count <= 30 THEN 2
#             ELSE 1
#         END as freq
#     WITH freq+level as degree, rule_count
#     WITH rule_count,
#         CASE
#             WHEN 7<= degree <= 8 THEN 4
#             WHEN 5<= degree <= 6 THEN 3
#             WHEN 3<= degree <= 4 THEN 2
#             ELSE 1
#         END AS threat_level
#     WITH COLLECT({{threat_level: threat_level, rule_count: rule_count}}) as data, sum(rule_count) as num_threat_levels
#     UNWIND data as item
#     WITH sum((item.threat_level*item.rule_count)) as total_threat_levels, num_threat_levels, data
#     UNWIND data as item
#     WITH toInteger(round(toFloat(total_threat_levels)/num_threat_levels)) as average, item
#     WITH sum(item.rule_count) as count, item.threat_level as level, average
#     RETURN average, level, count
#     """
#     results = graph.run(cypher)
#     data =[0,0,0,0]
#     for result in results:
#         average = result['average']
#         level = result['level']
#         data[level-1] = result['count']
#     degree = [3.20, 3.73, 4.25, 4.85]
#     color = ['#1cc88a', '#f6c23e', '#fd7e14', '#e74a3b']
#     average = {'degree': degree[average-1], 'color': color[average-1]}
#     response = {'senario': {'average': json.dumps(average), 'count': (data)}}
#     return response

# # 최근 탐지 위협 (neo4j graph 연동)
# def get_recent_threat():
#     global graph
#     cypher = '''
#         MATCH (l:LOG)-[d:FLOW_DETECTED]->(r:RULE{is_allow:1})
#         RETURN
#         id(d) AS No,
#         head([label IN labels(l) WHERE label <> 'LOG']) AS cloud,
#         head([label IN labels(l) WHERE label <> 'LOG'])+'/'+l.sourceIp AS system,
#         r.name AS detected_rule,
#         r.name+'#'+id(d) AS rule_name,
#         l.actionDisplayName AS action,
#         l.eventTime AS eventTime,
#         apoc.date.format(l.eventTime,'ms', 'yyyy-MM-dd HH:mm:ss', 'Asia/Seoul') AS etime
#         ORDER BY eventTime DESC
#         LIMIT 10
#     '''
#     results = graph.run(cypher)
#     data_list = []
#     filter = ['cloud', 'detected_rule', 'rule_name', 'eventTime']
#     for result in results:
#         # Change to type dictionary
#         data = dict(result.items())
#         form_dict = {}
#         for key in filter:
#             if key != 'detected_rule':
#                 value = data.pop(key)
#             else:
#                 value = data[key]
#             form_dict[key] = value
#         data['form'] = form_dict
#         data_list.append(data)
#     context = {'recent_threat': data_list}
#     return context