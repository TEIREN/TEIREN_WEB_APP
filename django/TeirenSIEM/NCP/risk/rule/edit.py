from django.conf import settings
from py2neo import Graph, ClientError

host = settings.NEO4J_HOST
port = settings.NEO4J_PORT
password = settings.NEO4J_PASSWORD
username = settings.NEO4J_USERNAME
graph = Graph(f"bolt://{host}:{port}", auth=(username, password))

## Edit Rule Modal
# List Edit Rule Details (For Edit Rule Modal)
def get_edit_rule_page(request):
    rule_type = request['log_type']
    og_rule_name = request['rule_name']
    cloud = request['cloud']
    global graph
    response ={}
    if rule_type == 'FLOW':
        cypher = f"""
            MATCH (r:RULE:FLOW:{cloud}{{name:'{og_rule_name}'}})
            RETURN r
        """
        results = graph.run(cypher)
        for result in results:
            flow = dict(result['r'].items())
            rule = {}
            for key, value in flow.items():
                if key.startswith('rule') and key != 'rule_type' and key != 'rule_id':
                    rule.update({key:value})
            flow.update({'rule': rule})
        flow.update({'request': request})
        response = {'flow': flow}
        cypher = f"""
            MATCH (r:RULE:{cloud})
            WHERE NOT 'FLOW' IN labels(r)
            RETURN distinct(r.name) as actions
        """
        results = graph.run(cypher)
        actions = []
        for result in results:
            actions.append(result['actions'])
        response.update({'actions': actions})
    else:
        cypher = f"""
            MATCH (r:RULE:{cloud}{{name:'{og_rule_name}', productName:'{rule_type}'}})
            RETURN r
        """
        results = graph.run(cypher)
        for result in results:
            normal = dict(result['r'].items())
            if 'timeRange' in normal and normal['timeRange'] != 0 :
                time = timerange_to_timedict(normal['timeRange'])
                normal.update({'time': time })
        normal.update({'request': request})
        response.update({'normal': normal })
        cypher = f"""
            MATCH (r:RULE:{cloud})
            WHERE NOT 'FLOW' IN labels(r)
            RETURN distinct(r.productName) as types
        """
        results = graph.run(cypher)
        types = []
        for result in results:
            if result['types'] != rule_type and result['types'] != 'All':
                types.append(result['types'])
        response.update({'types': types})
    return response

# Edit Rule Action
def edit_rule(request):
    og_name = request['og_rule_name']
    cloud = request['cloud']
    is_flow = request['is_flow']
    id = request['rule_id']
    if is_flow == '0':
        global graph
        cypher = f"""
            MATCH (r:RULE:{cloud} {{name:'{og_name}'}})
            WHERE id(r) = {int(id)}
            RETURN r
        """
        results = graph.run(cypher)
        for result in results:
            node = result['r']
        time = {}
        time_filter = ['days', 'hours', 'minutes', 'seconds']
        filter = ['og_rule_name', 'on_off', 'cloud', 'is_flow', 'rule_id']
        for key, value in request.items():
            if value:
                if key in time_filter:
                    time[key] = value
                    continue
                if key in filter:
                    continue
                if key == 'name':
                    if value != og_name:
                        check = graph.evaluate(f"""
                            MATCH (n:RULE:{cloud} {{name:'{value}'}}) 
                            RETURN n 
                            LIMIT 1
                        """) is not None
                        if check:
                            return '이미 존재하는 정책 이름입니다.'
                node[key] = value
        time = timedict_to_timerange(time)
        if time > 0:
            node['timeRange'] = time
        try:
            graph.push(node)
            response = '정책 수정 성공'
        except ClientError as e:
            response = '정책 수정 실패'
    else:
        cypher = f"""
            MATCH (r:RULE:FLOW:{cloud} {{name:'{og_name}'}})
            WHERE id(r) = {int(id)}
            RETURN r
        """
        node = graph.evaluate(cypher)
        filters = ['csrf', 'og', 'cloud', 'is_flow', 'rule_id']
        for key, value in request.items():
            if value:
                if any(key.startswith(filter) for filter in filters):
                    continue
                if key == 'name':
                    if value != og_name:
                        check = graph.evaluate(f"""
                            MATCH (n:RULE:{cloud} {{name:'{value}'}}) 
                            RETURN n 
                            LIMIT 1
                        """) is not None
                        if check:
                            return '이미 존재하는 정책 이름입니다.'
                node[key] = value
        try:
            graph.push(node)
            response = '정책 수정 성공'
        except ClientError as e:
            response = '정책 수정 실패'
    return response

# Add Action in Edit Rule Modal
def edit_rule_add_action(request):
    cloud = request['cloud']
    count = int(request['count']) +1
    global graph
    cypher = f"""
    MATCH (r:RULE:{cloud})
    WHERE NOT 'FLOW' IN labels(r)
    WITH distinct(r.name) as actions
    RETURN COLLECT(actions) as actions
    """
    results = graph.run(cypher)
    for result in results:
        actions = result
    response = {'count': count, 'actions': actions[0]}
    return response

# Change Epoch To Time
def timerange_to_timedict(timerange):
    time = int(timerange / 1000)
    seconds = int(time)
    minutes = int(seconds/60)
    hours = int(minutes/60)
    days = int(hours/24)
    seconds = int(seconds % 60)
    minutes = int(minutes % 60)
    hours = int(hours % 24)
    response = {
        'seconds': seconds,
        'minutes': minutes,
        'hours': hours,
        'days': days
    }
    return response

# Change Time to Epoch
def timedict_to_timerange(time):
    days = int(time['days']) if 'days' in time else 0
    hours = int(time['hours']) if 'hours' in time else 0
    minutes = int(time['minutes']) if 'minutes' in time else 0
    seconds = int(time['seconds']) if 'seconds' in time else 0
    days *= 86400
    hours *= 3600
    minutes*= 60
    result = days+hours+minutes+seconds
    result *= 1000
    response = result
    return response