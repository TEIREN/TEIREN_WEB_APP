# local
import json
from common.neo4j.handler import Neo4jHandler
## class handler
from .add import Add
from .delete import Delete

# django
from django.conf import settings

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


class Edit(Neo4jHandler):
    def __init__(self, request) -> None:
        super().__init__()
        self.request_ = request
        self.request = dict(request.POST.items()) if request.method == 'POST' else dict(request.GET.items())
        self.user_db = request.session.get('db_name')
        
    ## Edit Rule Modal
    # List Edit Rule Details (For Edit Rule Modal)
    def get_edit_rule_page(self):
        rule_type = self.request['ruleClass']
        if rule_type == 'Dynamic':
            response = self.dynamic_edit_rule_page()
        else:
            response = self.static_edit_rule_page()
        return response

    def static_edit_rule_page(self):
        rule_type = self.request['ruleClass']
        og_rule_name = self.request['rule_name']
        rule_id = self.request['rule_id']
        logType = self.request['log_type']
        response ={}
        cypher = f"""
        MATCH (rule:Rule:{logType} {{ruleName:'{og_rule_name}', ruleClass:'static'{f", eventSource:'{rule_type}.amazonaws.com'" if rule_type != 'All' else ""}}})
        WHERE ID(rule) = {rule_id}
        UNWIND KEYS(rule) as key
        WITH key, rule
        WHERE key IN ['ruleKeys', 'ruleValues', 'ruleOperators', 'ruleLogicals']
        WITH DISTINCT(key) as key, rule
        WITH rule, key, COLLECT(rule[key]) AS values
        UNWIND values AS val_list
        UNWIND range(0,size(val_list)-1) AS index
        WITH rule, index, apoc.map.fromPairs(COLLECT([key, val_list[index]])) AS properties
        WITH rule, COLLECT(properties) AS properties
        RETURN
            rule.ruleName as ruleName,
            rule.ruleComment as ruleComment,
            rule.ruleCount as ruleCount,
            rule.timeRange as timeRange,
            rule.level as level,
            CASE rule.level
                WHEN 1 THEN 'LOW'
                WHEN 2 THEN 'MID'
                WHEN 3 THEN 'HIGH'
                ELSE 'CRITICAL' 
            END as level_label,
            properties
        """
        results = self.run_data(database=self.user_db, query=cypher)
        response.update({'static': results[0] })
        return response

    def dynamic_edit_rule_page(self):
        og_rule_name = self.request['rule_name']
        rule_id = self.request['rule_id']
        logType = self.request['log_type']
        cypher = f"""
        MATCH (rule:Rule:{logType} {{ruleName:'{og_rule_name}', ruleClass:'dynamic'}})
        WHERE ID(rule) = {rule_id}
        UNWIND KEYS(rule) as keys
        WITH rule, keys
        WHERE keys =~ 'flow.*'
        WITH rule, keys ORDER BY keys
        WITH rule, rule[keys] as flowName
        MATCH (flow:Flow{{flowName:flowName}})
        WITH rule, flow
        UNWIND KEYS(flow) as key 
        WITH rule, flow, key
        WHERE NOT key IN ['flowName', 'flowComment', 'count']
        WITH rule, flow, COLLECT(key) as keys
        WITH rule, flow, keys, [key IN keys | flow[key]] AS vals
        WITH rule, {{flowName:flow.flowName, flowComment:flow.flowComment, keys: keys, values:vals}} as flows, flow
        WITH rule,
            CASE
                WHEN flow.count IS NULL THEN flows
                ELSE apoc.map.merge(flows, {{count:flow.count}})
            END AS flows
        RETURN
            rule.ruleName as ruleName,
            rule.ruleComment as ruleComment,
            rule.timeRange as timeRange,
            rule.wheres as wheres,
            rule.level as level,
            CASE rule.level
                WHEN 1 THEN 'LOW'
                WHEN 2 THEN 'MID'
                WHEN 3 THEN 'HIGH'
                ELSE 'CRITICAL'
            END as level_label,
            COLLECT(flows) as flows
        """
        results = self.run_data(database=self.user_db, query=cypher)
        for result in results:
            dynamic = dict(result)
            dynamic['wheres'] = json.dumps([parse_dict(s) for s in dynamic.pop('wheres')])
            break
        return {'dynamic': dynamic}


    # Edit Rule Action
    def edit_rule(self):
        if self.request['ruleClass'] == 'static':
            return self.edit_static_rule()
        else:
            return self.edit_dynamic_rule()

    def edit_static_rule(self):
        self.request['count'] = 1
        ruleName = self.request['ruleName']
        og_ruleName = self.request['og_rule_name']
        logType = self.request['log_type']
        
        cypher = f"""
        MATCH (rule:Rule:{logType} {{ruleName: '{ruleName}'}})
        RETURN COUNT(rule) AS count
        """
        result = self.run(database=self.user_db, query=cypher)
        
        if ruleName != og_ruleName and result['count'] > 0:
            return f"'{ruleName}' Already Existing Rule Name"
        
        self.request['check'] = 1
        with Add(self.request_) as __add:
            response = __add.add_static_rule(request=self.request)
            if response['status'] != 'success':
                return 'Fail to Add rule'
        with Delete(self.request_) as __delete:
            response = __delete.delete_static_rule(request=self.request)
            if response['status'] == 'success':
                return response['message']
            
        return 'Unknown Error'

    def edit_dynamic_rule(self):
        ruleName = self.request['ruleName']
        og_ruleName = self.request['og_rule_name']
        logType = self.request['log_type']
        
        cypher = f"""
        MATCH (rule:Rule:{logType} {{ruleName: '{ruleName}'}})
        RETURN COUNT(rule) AS count
        """
        result = self.run(database=self.user_db, query=cypher)
        
        if ruleName != og_ruleName and result['count'] > 0:
            return f"'{ruleName}' Already Existing Rule Name"
        
        self.request['check'] = 1
        with Add(self.request_) as __add:
            response = __add.add_dynamic_rule(request=self.request)
            if response['status'] != 'success':
                return 'Fail to Dynamic rule'
        
        with Delete(self.request_) as __delete:
            response = __delete.delete_dynamic_rule(request=self.request)
            if response['status'] == 'success':
                return response['message']
            
        return 'Unknown Error'
    

def parse_dict(s):
    s = s.strip('{}')
    items = s.split(', ')
    d = {}
    for item in items:
        key_value = item.split(':')
        d[key_value[0]] = key_value[1]
    return d

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