from django.conf import settings
from py2neo import Graph, ClientError

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

## Add Rule Modal
# Get Log Properties for Adding Custom Rule
def get_log_properties(request):
    cloud = request['cloud']
    global graph
    cypher = f"""
    MATCH (l:Log:{cloud})-[:DETECTED]->()
    WITH KEYS(l) AS keys
    RETURN apoc.coll.toSet(REDUCE(res = [], k IN COLLECT(DISTINCT(keys)) | res + k)) AS property
    """
    results = graph.evaluate(cypher)
    return results

# List Default Rule Actions for Adding Custom Rule
def get_default_actions(request):
    cloud = request['cloud']
    global graph
    cypher = f"""
        MATCH (r:Rule:{cloud})
        WHERE NOT 'FLOW' in LABELS(r)
        RETURN r.ruleName as ruleName
    """
    results = graph.run(cypher)
    response = []
    for result in results:
        response.append(result['ruleName'])
    return response

# Add Rule Action
def add_rule(request):
    global graph
    count = request['count']
    cloud = request['cloud']
    rules = {}
    # 입력된 정책 전처리
    for key, value in request.items():
        for i in range(1,int(count)+1):
            if key.endswith('_'+str(i)):
                ## 입력 오류 확인
                if 'eventSource' in key:
                    if value == "로그 종류":
                        return f"[{i}번 째 행위] 로그 종류를 선택해주세요"
                elif 'ruleName' in key:
                    if not value:
                        return f"[{i}번 째 행위] 정책 이름을 입력해주세요"
                    elif value == "행위 선택":
                        return f"[{i}번 째 행위] 행위를 선택해주세요"
                    else:
                        if rules[str(i)]['ruleType'] == 'custom':
                            cypher = f"MATCH (r:RULE:{cloud} {{ruleName:'{value}'}}) RETURN COUNT(r)"
                            result = graph.evaluate(cypher)
                            if result:
                                return f"[{i}번 째 행위] 같은 이름의 정책이 존재합니다"
                elif 'ruleComment' in key:
                    if not value:
                         return f"[{i}번 째 행위] 정책 설명을 입력해주세요"
                elif 'key' in key:
                    if value:
                        rules[str(i)][f"property{key[-3]}"] = value
                        continue
                    else:
                        return f"[{i}번 째 행위] 새로운 정책 특성 {key[-3]}을 입력해주세요"
                elif 'val' in key:
                    if not value:
                        return f"[{i}번 째 행위] 정책 특성 값 {key[-3]}을 입력해주세요"
                elif f"custom_{i}" in key:
                    if value == f"정책 특성 {key[-3]}":
                        return f"[{i}번 째 행위] 정책 특성 {key[-3]}을 선택해주세요"
                ## 오류 없는 입력된 값 저장
                if value:
                    if str(i) not in rules:
                        rules[str(i)] = {}
                    if value == 'new':
                        value = 'custom'
                    rules[str(i)].update({key[:-2]:value})

    merge_cypher = ''
    is_flow = 0
    # IF FLOW RULE
    if 'ruleType' in request:
        eventSource = []
        is_flow = 1
        if not request['ruleName']:
            return "FLOW 정책의 이름을 입력해주세요"
        elif request['ruleName']:
            cypher = f"MATCH (r:RULE:{cloud} {{ruleName: '{request['ruleName']}'}}) RETURN COUNT(r)"
            result = graph.evaluate(cypher)
            if result > 0:
                return "FLOW 정책과 같은 이름의 정책이 존재합니다"
        elif not request['ruleComment']:
            return "FLOW 정책의 설명을 입력해주세요"
        elif request['blank']:
            try:
                blank = int(request['blank'])
            except:
                return "FLOW 정책의 기타 행위 허용수는 숫자로만 입력 가능합니다."
        flow_cypher = f"""
        MERGE (f:FLOW:RULE:{cloud}{{
            ruleName:'{request['ruleName']}',
            ruleComment:'{request['ruleComment']}',
            ruleType: 'custom',
            blank:{blank if request['blank'] else 0},
            level: 4,
            on_off: 1,
        """
    # 최종 쿼리 제작
    for i, (_, rule) in enumerate(rules.items(), start=1):
        ## IF DEFAULT RULE
        if rule['ruleType'] == 'default':
            if len(rules) == 1:
                return '정책을 추가해주세요.'
            if i == 1:
                cypher = f"MATCH (r{i}:RULE:{cloud} {{ruleName:'{rule['ruleName']}'}})"
            else:
                cypher = f"WITH * MATCH (r{i}:RULE:{cloud} {{ruleName:'{rule['ruleName']}'}})"
            merge_cypher += cypher
            # IF FLOW -> ADD EVENTSOURCE
            if is_flow:
                cypher += f"RETURN r{i}.eventSource"
                results = graph.evaluate(cypher)
                eventSource.append(results)
                flow_cypher += f"rule{i}: r{i}.ruleName, "
        ## IF CUSTOM RULE
        elif rule['ruleType'] == 'custom':
            cypher = f"""
            MERGE (r{i}:RULE:{cloud}{{
                level: 2,
                on_off: 1,
            """
            prop = {}
            for key, value in rule.items():
                if 'val' in key:
                    cypher += f"{prop_key}: '{value}', "
                    del prop_key
                elif 'property' in key:
                    if value in prop:
                        prop[value] += 1
                        value = f"{value}{prop[value]}"
                    else:
                        prop[value] = 1
                    prop_key = value
                elif 'eventSource' in key:
                    value = f"{value}.amazonaws.com"
                    cypher += f"{key}: '{value}', "
                else:
                    cypher += f"{key}: '{value}', "
                # IF FLOW -> ADD EVENTSOURCE
                if key == 'eventSource' and is_flow:
                        eventSource.append(value)
                        flow_cypher += f"rule{i}:r{i}.ruleName,\n"
            cypher = f"{cypher[0:-2]}}})"
            merge_cypher += cypher
    # IF FLOW -> ADD EVENTSOURCE
    if is_flow:
        flow_cypher += 'eventSource:\''
        for source in eventSource:
            flow_cypher += f"{source},"
        flow_cypher = flow_cypher[:-1]+"'})"
        merge_cypher += flow_cypher
    try:
        graph.evaluate(merge_cypher)
        return '정책 추가 완료'
    except ClientError as e:
        return '정책 추가 실패'