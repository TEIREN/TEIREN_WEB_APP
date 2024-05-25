# 리눅스 버전
### 룰셋추가
```sh
curl -X POST "http://localhost:8888/ruleset/" -H "Content-Type: application/json" -d '{
    "name": "Detect systemd info messages",
    "system": "linux",
    "query": {
        "query": {
            "bool": {
                "must": [
                    {
                        "match": {
                            "message": "system activity accounting tool"
                        }
                    },
                    {
                        "match": {
                            "programname": "systemd"
                        }
                    }
                ]
            }
        }
    },
    "severity": 4
}'
```

### 탐지된 결과 확인 (리눅스)
```sh
curl -X GET "localhost:9200/detected_logs/_search?pretty"
```

1. 리눅스 버전으로 네이밍 변경
2. 다른 버전도 만들기
