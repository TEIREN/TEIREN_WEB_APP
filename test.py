import pymssql

# 데이터베이스 연결 설정
conn = pymssql.connect(
    server='3.35.81.217',
    user='SA',
    password='Qwer1234',
    database='study'
)
cursor = conn.cursor()

# 테이블 구조 확인
cursor.execute("SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'companyinfo'")
columns = cursor.fetchall()

# 출력
for column in columns:
    print(column)

cursor.close()
conn.close()
