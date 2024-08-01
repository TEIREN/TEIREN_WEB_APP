import requests
import json

class MySQLIntegartion:
    def __init__(self, request:dict):
        self.integration = request.pop('integration_type', '')
        self.request = request
    
    # Elasticsearch Server에 연동하기 전에 예외처리 및 파싱 (TCP/UDP => fluentd)
    def check_network(self):
        """
        self.request =
        {'server_ip': '', 'dst_port': '', 'tag_name': ''}
        """
        return {"error": "Network Transmission Not Ready. Please Use DB Connection."}
        if any(val == '' for val in self.request.values()):
            return {"error": "Please Insert All Required Items."}
        return self.insert_network()
    
    # Elasticsearch Server에 연동하기 전에 예외처리 및 파싱 (API)
    def check_account(self):
        """
        self.request = 
        {'server_ip': '', 'db_server': '', 'db_name': '', 'db_uid': '', 'db_password': '', 'db_table': '', 'tag_name': ''}
        """
        try:
            if any(val == '' for val in self.request.values()):
                return {"error": "Please Insert All Required Items."}
            return self.insert_account()
        except Exception as e:
            print(e)
            return {"error": "Please reload and try again."}
    
    # Elasticsearch Server에 연동하기 (TCP/UDP => fluentd)
    def insert_network(self):
        """
        self.request =
        {'server_ip': '', 'dst_port': '', 'tag_name': ''}
        """
        message_data = {
            "Teiren Server IP": self.request['server_ip'],
            "Destination Port": self.request['dst_port'],
            "Tag Name": self.request['tag_name'],
        }
        try:
            url = f"http://{self.request['server_ip']}:8088/collector/add/mysql/{self.request['tag_name']}"
            headers = {
                "Content-Type": "application/json"
            }
            data = {
                "new_protocol": "udp",
                "new_source_ip": "0.0.0.0",
                "new_dst_port": self.request['dst_port'],
                "new_log_tag": self.request['tag_name'],
                "integration_type": self.integration
            }
            # response = requests.post(url=url, headers=headers, json=data)
            # print(response.json)
            response = {"message": f"Successfully Integrated MySQL: \n{message_data}"}
        except Exception as e:
            print(e)
            response = {"error": f"Failed to Integrate MySQL: \n{message_data}"}
        finally:
            return response
    
    def insert_account(self):
        message_data = {
            "Teiren Server IP":self.request['server_ip'],
            "MySQL Server IP":self.request['db_server'],
            "Database Name":self.request['db_name'],
            "User ID":self.request['db_uid'],
            "User Password":self.request['db_password'],
            "Table Name": self.request['db_table'],
        }
        try:
            url = f"http://{self.request['server_ip']}:8088/collector/add/mysql/{self.request['tag_name']}"
            headers = {
                "content-type": "application/json"
            }
            data = {
                "host":self.request['db_server'],
                "user":self.request['db_uid'],
                "password":self.request['db_password'],
                "database":self.request['db_name'],
                "table_name": self.request['db_table'],
                "teiren_server_ip": self.request['server_ip'],
                "integration_type": self.integration
            }
            # response = requests.post(url=url, headers=headers, json=data)
            if 'message' in response.json():
                response = {"message": f"Successfully Integrated MySQL: \n{message_data}"}
            else:
                raise Exception
        except Exception as e:
            print(e)
            response = {"error": f"Failed to Integrate MySQL: \n{message_data}"}
        finally:
            return response

def mysql_insert(request):
    try:
        if request.POST.get('integration_type', '') == '':
            return 'Please reload the page and try again.'
        integration =  MySQLIntegartion(request=request.POST.dict())
        response = getattr(integration, f'check_{integration.integration}')()
    except Exception as e:
        print(e)
        response = {"error": "Please reload and try again."}
    finally:
        return json.dumps(response)