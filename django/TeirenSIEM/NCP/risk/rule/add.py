from django.conf import settings
from py2neo import Graph, ClientError

host = settings.NEO4J_HOST
port = settings.NEO4J_PORT
password = settings.NEO4J_PASSWORD
username = settings.NEO4J_USERNAME
graph = Graph(f"bolt://{host}:{port}", auth=(username, password))

## Add Rule Modal
# List Log Types(productName) for Adding Custom Rule
def get_custom_log_types(request):
    cloud = request['cloud']
    global graph
    cypher = f"""
        MATCH (r:RULE:{cloud})
        WITH DISTINCT(r.productName) as pn
        WHERE NOT pn CONTAINS ',' and pn <> 'All'
        RETURN pn
    """
    response = []
    results = graph.run(cypher)
    for result in results:
        response.append(result['pn'])
    return response

# List Default Rule Actions for Adding Custom Rule
def get_default_actions(request):
    cloud = request['cloud']
    global graph
    cypher = f"""
        MATCH (r:RULE:{cloud} {{rule_type: 'default'}})
        RETURN r.name as name
    """
    results = graph.run(cypher)
    response = []
    for result in results:
        response.append(result['name'])
    return response

# Add Rule Action
def add_rule(request):
    count = request['count']
    cloud = request['cloud']
    rules = {}
    # return request.items()
    for key, value in request.items():
        for i in range(1,int(count)+1):
            if key.endswith('_'+str(i)):
                if value:
                    if str(i) not in rules:
                        rules[str(i)] = {}
                    if value == 'new':
                        value = 'custom'
                    rules[str(i)].update({key[:-2]:value})
    merge_cypher = ''
    is_flow = 0
    time = {}
    time_filter = ['seconds', 'minutes', 'hours', 'days']
    int_filter = ['subAccountNo', 'count', 'portRange', 'eventTime', 'on_off']
    if 'rule_type' in request:
        productName = []
        is_flow = 1
        if not request['name']:
            return "FLOW 정책의 이름을 입력해주세요"
        elif graph.evaluate(f"""
                MATCH (n:RULE:{cloud} {{name:'{request['name']}'}}) 
                RETURN n 
                LIMIT 1
            """) is not None:
            return "FLOW 정책과 같은 이름의 정책이 존재합니다."
        elif not request['comment']:
            return "FLOW 정책의 설명을 입력해주세요"
        elif request['blank']:
            try:
                blank = int(request['blank'])
            except:
                return "FLOW 정책의 기타 행위 허용수는 숫자로만 입력 가능합니다."
        flow_cypher =f"""
        MERGE (f:FLOW:RULE:{cloud}{{name:'{request['name']}',
        comment:'{request['comment']}',
        rule_type: 'custom',
        blank:{blank if request['blank'] else 0},
        alert_email1:'{request['alert_email1']}',
        alert_email2:'{request['alert_email2']}',
        on_off: 1,
        is_allow:1,\n
        """
    for i, (_, rule) in enumerate(rules.items(), start=1):
        if rule['rule_type'] == 'default':
            if len(rules) == i:
                return '새로운 정책을 생성하세요.'
            cypher = f"MATCH (n{i}:RULE:{cloud}{{name:'{rule['name']}'}})\n"
            merge_cypher += cypher
            if is_flow:
                cypher += f"RETURN n{i}.productName as pn"
                results = graph.run(cypher)
                for result in results:
                    productName.append(result['pn'])
                flow_cypher += f"rule{i}:n{i}.name,\n"
        else:
            if 'name' not in rule:
                return f"{i}번째 정책의 이름을 입력해주세요"
            elif graph.evaluate(f"""
                    MATCH (n:RULE:{cloud} {{name:'{rule['name']}'}}) 
                    RETURN n 
                    LIMIT 1
                """) is not None:
                return f"{i}번째 정책과 같은 이름의 정책이 존재합니다."
            elif 'comment' not in rule:
                return f"{i}번째 정책의 설명을 입력해주세요"
            elif rule['productName'] == '로그 종류':
                return f"{i}번째 정책의 로그종류를 입력해주세요"
            rule['on_off'] = 1
            rule['is_allow'] = 0
            cypher = f"MERGE (n{i}:RULE:{cloud}{{\n"
            for key, value in rule.items():
                if key in time_filter:
                    time[key] = value
                elif key in int_filter:
                    try:
                        cypher += f"  {key}:{int(value)} ,\n"
                    except:
                        return f"{key}는 숫자로만 입력 가능합니다."
                else:
                    if key == 'productName' and is_flow:
                        productName.append(value)
                        flow_cypher += f"rule{i}:n{i}.name,\n"                    
                    cypher += f"  {key}:'{value}' ,\n"
            merge_cypher += cypher[:-2]+'})\n'
    if is_flow:
        flow_cypher += 'productName:\''
        for product in productName:
            flow_cypher += f"{product},"
        flow_cypher = flow_cypher[:-1]+"'})"
        merge_cypher += flow_cypher
    try:
        graph.evaluate(merge_cypher)
        return '정책 추가 완료'
    except ClientError as e:
        return '정책 추가 실패'