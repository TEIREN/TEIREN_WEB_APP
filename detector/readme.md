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
### 룰셋 확인 (리눅스)
```sh
curl -X GET "localhost:9200/linux_ruleset/_search?pretty"
```

### 탐지된 결과 확인 (리눅스)
```sh
curl -X GET "localhost:9200/linux_detected_log/_search?pretty"
```

# 개발중
```sh
curl -X POST "http://localhost:8888/ruleset/?index_choice=1" -H "Content-Type: application/json" -d '{
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

1. index.py
-  index 생성
- 생성 된지 확인하려면 curl -X GET "localhost:9200/_cat/indices?v"
2. input_ruleset.py
- 룰셋정보를 직접 입력
3. 현재 룰셋이 생성이 되어도 detector.py에서 탐지를 못함 