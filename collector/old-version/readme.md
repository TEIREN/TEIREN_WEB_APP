### 전체 시스템에 대한 엔드포인트 및 예시

무조건 sudo 권한으로 앱을 실행시켜야한다.

모든 시스템에 대해 동일한 패턴을 사용하여 로그 수집, 중지, 재개, 상태 확인 및 API 키 삭제를 처리한다. 각 시스템의 `TAG_NAME`을 적절히 설정해주면 된다.

#### Linux

##### 1. 로그 수집 시작

```sh
curl -X POST "http://localhost:8000/linux_log" -H "Content-Type: application/json" -d '{"logs": [{"example_log_key": "example_log_value"}]}'
```

##### 2. 로그 수집 중지

```sh
curl -X POST "http://localhost:8000/stop_linux_log" -H "Content-Type: application/json" -d '{"TAG_NAME": "linux"}'
```

##### 3. 로그 수집 재개

```sh
curl -X POST "http://localhost:8000/resume_linux_log" -H "Content-Type: application/json" -d '{"TAG_NAME": "linux"}'
```

##### 4. API 키 삭제 (중지 상태에서만 가능)

```sh
curl -X POST "http://localhost:8000/delete_linux_api_key" -H "Content-Type: application/json" -d '{"TAG_NAME": "linux"}'
```

##### 5. 상태 확인

```sh
curl -X POST "http://localhost:8000/log_collection_status" -H "Content-Type: application/json" -d '{"TAG_NAME": "linux"}'
```

#### Window

##### 1. 로그 수집 시작

```sh
curl -X POST "http://localhost:8000/win_log" -H "Content-Type: application/json" -d '{"logs": [{"example_log_key": "example_log_value"}]}'
```

##### 2. 로그 수집 중지

```sh
curl -X POST "http://localhost:8000/stop_win_log" -H "Content-Type: application/json" -d '{"TAG_NAME": "window"}'
```

##### 3. 로그 수집 재개

```sh
curl -X POST "http://localhost:8000/resume_win_log" -H "Content-Type: application/json" -d '{"TAG_NAME": "window"}'
```

##### 4. API 키 삭제 (중지 상태에서만 가능)

```sh
curl -X POST "http://localhost:8000/delete_win_api_key" -H "Content-Type: application/json" -d '{"TAG_NAME": "window"}'
```

##### 5. 상태 확인

```sh
curl -X POST "http://localhost:8000/log_collection_status" -H "Content-Type: application/json" -d '{"TAG_NAME": "window"}'
```

#### Genian

##### 1. 로그 수집 시작

```sh
curl -X GET "http://localhost:8000/genian_api_send?api_key=your_api_key&TAG_NAME=genian_api"
```

##### 2. 로그 수집 중지

```sh
curl -X POST "http://localhost:8000/stop_genian_api_send" -H "Content-Type: application/json" -d '{"TAG_NAME": "genian_api"}'
```

##### 3. 로그 수집 재개

```sh
curl -X POST "http://localhost:8000/resume_genian_api_send" -H "Content-Type: application/json" -d '{"TAG_NAME": "genian_api"}'
```

##### 4. API 키 삭제 (중지 상태에서만 가능)

```sh
curl -X POST "http://localhost:8000/delete_genian_api_key" -H "Content-Type: application/json" -d '{"TAG_NAME": "genian_api"}'
```

##### 5. 상태 확인

```sh
curl -X POST "http://localhost:8000/log_collection_status" -H "Content-Type: application/json" -d '{"TAG_NAME": "genian_api"}'
```

#### Fortigate

##### 1. 로그 수집 시작

```sh
curl -X GET "http://localhost:8000/fortigate_api_send?api_key=your_api_key&TAG_NAME=fortigate_api"
```

##### 2. 로그 수집 중지

```sh
curl -X POST "http://localhost:8000/stop_fortigate_api_send" -H "Content-Type: application/json" -d '{"TAG_NAME": "fortigate_api"}'
```

##### 3. 로그 수집 재개

```sh
curl -X POST "http://localhost:8000/resume_fortigate_api_send" -H "Content-Type: application/json" -d '{"TAG_NAME": "fortigate_api"}'
```

##### 4. API 키 삭제 (중지 상태에서만 가능)

```sh
curl -X POST "http://localhost:8000/delete_fortigate_api_key" -H "Content-Type: application/json" -d '{"TAG_NAME": "fortigate_api"}'
```

##### 5. 상태 확인

```sh
curl -X POST "http://localhost:8000/log_collection_status" -H "Content-Type: application/json" -d '{"TAG_NAME": "fortigate_api"}'
```

#### MSSQL

##### 1. 로그 수집 시작

```sh
curl -X POST "http://localhost:8000/start_mssql_collection" -H "Content-Type: application/json" -d '{
  "server": "your_server",
  "database": "your_database",
  "username": "your_username",
  "password": "your_password",
  "table_name": "your_table_name",
  "TAG_NAME": "mssql_api"
}'
```

##### 2. 로그 수집 중지

```sh
curl -X POST "http://localhost:8000/stop_mssql_api_send" -H "Content-Type: application/json" -d '{"TAG_NAME": "mssql_api"}'
```

##### 3. 로그 수집 재개

```sh
curl -X POST "http://localhost:8000/resume_mssql_api_send" -H "Content-Type: application/json" -d '{"TAG_NAME": "mssql_api"}'
```

##### 4. API 키 삭제 (중지 상태에서만 가능)

```sh
curl -X POST "http://localhost:8000/delete_mssql_api_key" -H "Content-Type: application/json" -d '{"TAG_NAME": "mssql_api"}'
```

##### 5. 상태 확인

```sh
curl -X POST "http://localhost:8000/log_collection_status" -H "Content-Type: application/json" -d '{"TAG_NAME": "mssql_api"}'
```

#### Fluentd Config

##### 1. 설정 추가

```sh
curl -X POST "http://localhost:8000/add_config" -H "Content-Type: application/json" -d '{
  "new_protocol": "tcp",
  "new_source_ip": "0.0.0.0",
  "new_dst_port": "24224",
  "new_log_tag": "fluentd_log"
}'
```

##### 2. 설정 중지

```sh
curl -X POST "http://localhost:8000/stop_fluentd_api_send" -H "Content-Type: application/json" -d '{"TAG_NAME": "fluentd_log"}'
```

##### 3. 설정 재개

```sh
curl -X POST "http://localhost:8000/resume_fluentd_api_send" -H "Content-Type: application/json" -d '{"TAG_NAME": "fluentd_log"}'
```

##### 4. 설정 삭제 (중지 상태에서만 가능)

```sh
curl -X POST "http://localhost:8000/delete_fluentd_api_key" -H "Content-Type: application/json" -d '{"TAG_NAME": "fluentd_log"}'
```

##### 5. 상태 확인

```sh
curl -X POST "http://localhost:8000/log_collection_status" -H "Content-Type: application/json" -d '{"TAG_NAME": "fluentd_log"}'
```

### Elasticsearch Index 예시

#### 1. Linux 로그 수집 예시

Index: `test_linux_syslog`

```json
{
  "_index": "test_linux_syslog",
  "_type": "_doc",
  "_id": "unique_id",
  "_source": {
    "example_log_key": "example_log_value",
    "TAG_NAME": "linux"
  }
}
```

#### 2. Window 로그 수집 예시

Index: `test_window_syslog`

```json
{
  "_index": "test_window_syslog",
  "_type": "_doc",
  "_id": "unique_id",
  "_source": {
    "example_log_key": "example_log_value",
    "TAG_NAME": "window"
  }
}
```

#### 3. Genian 로그 수집 예시

Index: `test_genian_syslog`

```json
{
  "_index": "test_genian_syslog",
  "_type": "_doc",
  "_id": "unique_id",
  "_source": {
    "example_log_key": "example_log_value",
    "TAG_NAME": "genian_api"
  }
}
```

#### 4. Fortigate 로그 수집 예시

Index: `test_fortigate_syslog`

```json
{
  "_index": "test_fortigate_syslog",
  "_type": "_doc",
  "_id": "unique_id",
  "_source": {
    "example_log_key": "example_log_value",
    "TAG_NAME": "fortigate_api

"
  }
}
```

#### 5. MSSQL 로그 수집 예시

Index: `test_mssql_syslog`

```json
{
  "_index": "test_mssql_syslog",
  "_type": "_doc",
  "_id": "unique_id",
  "_source": {
    "example_log_key": "example_log_value",
    "TAG_NAME": "mssql_api"
  }
}
```

#### 6. Fluentd Config 예시

Index: `userinfo`

```json
{
  "_index": "userinfo",
  "_type": "_doc",
  "_id": "unique_id",
  "_source": {
    "SYSTEM": "fluentd",
    "TAG_NAME": "fluentd_log",
    "inserted_at": "timestamp",
    "config": {
      "new_protocol": "tcp",
      "new_source_ip": "0.0.0.0",
      "new_dst_port": "24224",
      "new_log_tag": "fluentd_log"
    }
  }
}
```

