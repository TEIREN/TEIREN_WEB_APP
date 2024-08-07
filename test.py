import pymssql
import json

# 데이터베이스 연결 설정
conn = pymssql.connect(
    server='3.35.81.217',
    user='SA',  # SQL Server 인증을 사용할 경우 사용자 이름을 입력
    password='Qwer1234',  # SQL Server 인증을 사용할 경우 비밀번호를 입력
    database='study'
)
cursor = conn.cursor()

query = "SELECT * FROM companyinfo"
cursor.execute(query)

columns = [column[0] for column in cursor.description]
results = []
for row in cursor.fetchmany(10):
    results.append(dict(zip(columns, row)))

json_result = json.dumps(results, ensure_ascii=False, indent=4)

print(json_result)

cursor.close()
conn.close()
