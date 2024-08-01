# mysql_deployment.py
import pymysql
from fastapi import HTTPException
import datetime
import requests

class MySQLDeployment:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

    def connect(self):
        try:
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            print("==================")
            print("Successfully connected to MySQL")
            print("==================")
        except Exception as e:
            print("==================")
            print(f"Error connecting to MySQL: {str(e)}")
            print("==================")
            raise HTTPException(status_code=500, detail=f"Error connecting to MySQL: {str(e)}")

    def get_table_info(self):
        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT * FROM threads" # 이 부분을 하드 코딩 하지 말고 입력할 수 있도록 수정
                cursor.execute(sql)
                result = cursor.fetchall()
                print("==================")
                print(f"Fetched {len(result)} rows from MySQL")
                print("==================")
                return result
        except Exception as e:
            print("==================")
            print(f"Error fetching table info from MySQL: {str(e)}")
            print("==================")
            raise HTTPException(status_code=500, detail=f"Error fetching table info from MySQL: {str(e)}")
        finally:
            self.connection.close()
            print("==================")
            print("Closed MySQL connection")
            print("==================")

    async def save_integration(self, es_collector, config):
        await es_collector.save_integration(config)
        table_info = self.get_table_info()
        for row in table_info:
            log = {
                "request_ip": config["client_ip"],
                "client_hostname": config["client_hostname"],
                "TAG_NAME": es_collector.TAG_NAME,
                **{k: v for k, v in enumerate(row)}
            }
            await es_collector.es.index(index="mysql_syslog", document=log)
            print("==================")
            print(f"Indexed MySQL log: {log}")
            print("==================")

        # Automatically send logs to the collect_log endpoint
        collect_log_url = f"http://localhost:8088/collect_log/mysql/{es_collector.TAG_NAME}"
        try:
            response = requests.post(collect_log_url, json=table_info)
            print("==================")
            print(f"Sent logs to {collect_log_url}, response: {response.status_code}")
            print("==================")
        except Exception as e:
            print("==================")
            print(f"Error sending logs to {collect_log_url}: {str(e)}")
            print("==================")
