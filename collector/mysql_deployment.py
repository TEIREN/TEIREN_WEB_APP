# mysql_deployment.py

import pymysql

class MySQLDeployment:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.connect()

    def connect(self):
        try:
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            print("==================")
            print("MySQL connection established")
            print("==================")
        except Exception as e:
            print("==================")
            print(f"Error connecting to MySQL: {str(e)}")
            print("==================")
            raise

    def fetch_data(self, query):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
                print("==================")
                print(f"Fetched data: {result}")
                print("==================")
                return result
        except Exception as e:
            print("==================")
            print(f"Error fetching data: {str(e)}")
            print("==================")
            raise

    def close(self):
        if self.connection:
            self.connection.close()
            print("==================")
            print("MySQL connection closed")
            print("==================")
