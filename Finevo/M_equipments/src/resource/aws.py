from django.conf import settings
from common.neo4j.handler import Neo4jHandler
from botocore.exceptions import InvalidRegionError

def aws_check(request, logType):
    import boto3
    if request.method == 'POST':
        # 여기도 Form 처리 해야하는데 ....
        data = {}
        access_key = request.POST['access_key'].encode('utf-8').decode('iso-8859-1')  # 한글 입력 시 에러 발생 방지
        if access_key == '':
            data['class'] = 'btn btn-danger'
            data['value'] = 'Insert ACCESS KEY'
            return data
        secret_key = request.POST['secret_key'].encode('utf-8').decode('iso-8859-1')  # 한글 입력 시 에러 발생 방지
        if secret_key == '':
            data['class'] = 'btn btn-danger'
            data['value'] = 'Insert SECRET KEY'
            return data
        region_name = request.POST['region_name'].encode('utf-8').decode('iso-8859-1')
        if region_name == '':
            data['class'] = 'btn btn-danger'
            data['value'] = 'Insert REGION NAME'
            return data
        group_name = request.POST['group_name'].encode('utf-8').decode('iso-8859-1')
        if group_name == '':
            data['class'] = 'btn btn-danger'
            data['value'] = 'Insert LOG GROUP NAME'
            return data
        cypher = f"""
        MATCH (i:Integration)
        WHERE i.integrationType = 'Aws'
            AND i.accessKey = '{access_key}'
            AND i.secretKey = '{secret_key}'
            AND i.regionName = '{region_name}'
            AND i.groupName = '{group_name}'
        RETURN count(i) AS count
        """
        with Neo4jHandler() as neohandler:
            result = neohandler.run(database=request.session.get('db_name'), query=cypher)
        if result['count'] > 0:
            data['class'] = 'btn btn-warning'
            data['value'] = 'Already Registered Information'
            return data
        else:
            try:
                client = boto3.client(
                    f"{logType.lower() if logType == 'cloudtrail' else 'logs'}",
                    aws_access_key_id = access_key,
                    aws_secret_access_key = secret_key,
                    region_name=region_name
                )
            except InvalidRegionError:
                data['class'] = 'btn btn-danger'
                data['value'] = 'Invalid Region type (Try Again)'
                return data
            try:
                functionName = globals()[f"{group_name if group_name =='cloudtrail' else 'cloudwatch'}_check"]
                functionName(client, group_name)
                data['class'] = 'btn btn-success'
                data['value'] = ' ✓ Verified!'
                data['modal'] = {}
                data['modal']['access_key'] = access_key
                data['modal']['secret_key'] = secret_key
                data['modal']['region_name'] = region_name
                data['modal']['group_name'] = group_name
                
                return data
            except Exception:
                data['class'] = 'btn btn-danger'
                data['value'] = 'Failed To Verify (Try Again)'
                
                return data
    else:
        return {
            'class': 'btn btn-danger',
            'value': 'Failed To Verify (Try Again)'
        }

def cloudtrail_check(client, group_name):
    client.lookup_events()

def cloudwatch_check(client, group_name):
    if group_name == 'elb':
        return 0
    client.filter_log_events(
        logGroupName= group_name,
        limit = 1
    )

def aws_insert(request):
    if request.method == 'POST':
        integration_type = request.POST['modal_integration_type'].encode('utf-8').decode('iso-8859-1')
        access_key = request.POST['modal_access_key'].encode('utf-8').decode('iso-8859-1')
        secret_key = request.POST['modal_secret_key'].encode('utf-8').decode('iso-8859-1')
        region_name = request.POST['modal_region_name'].encode('utf-8').decode('iso-8859-1')
        log_type = request.POST['modal_log_type'].encode('utf-8').decode('iso-8859-1')
        group_name = request.POST['modal_group_name'].encode('utf-8').decode('iso-8859-1')
        cypher = f"""
        CREATE (i:Integration 
            {{
                integrationType:'{integration_type}',
                accessKey:'{access_key}', 
                secretKey:'{secret_key}',
                regionName: '{region_name}',
                logType: '{log_type}',
                groupName: '{group_name}',
                imageName: '{log_type.lower()}',
                isRunning: 0,
                container_id: 'None'
            }})
        RETURN COUNT(i) AS count
        """
        try:
            with Neo4jHandler() as neohandler:
                result = neohandler.run(database=request.session.get('db_name'), query=cypher)
            if result['count'] == 1:
                data = "Successfully Registered"
            else:
                raise Exception
        except Exception:
            data = "Failed To Register"
        finally:
            return data