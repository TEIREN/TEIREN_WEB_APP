# 리눅스 버전
1. prototype_main.py
2. linux_version.py
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
1. 
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

```sh
curl -X POST "http://3.35.81.217:9200/window_ruleset/_doc" -H 'Content-Type: application/json' -d'
{
    "name": "Detect VSS events",
    "system": "windows",
    "query": {
        "query": {
            "bool": {
                "must": [
                    {
                        "match": {
                            "EventID": 8224
                        }
                    },
                    {
                        "match": {
                            "SourceName": "VSS"
                        }
                    }
                ]
            }
        }
    },
    "severity": 3
}
'
```


++ 유연성을 확장시키여함 
추가할 기능 : 프러퍼티, 벨류, 추가 

1. 프러퍼티 ex : massage, programname
2. 벨류 ex : Starting sysstat-collect.service - system activity accounting tool..., systemd
3. 추가 : 프러퍼티를 추가하겠습니까? y -> 1번으로 다시 가 쿼리 추가 n -> 디텍터 생성