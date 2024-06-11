### 1. index.py
필요한 index 생성
```py
# 룰셋 인덱스 이름 매핑
ruleset_mapping = {
    1: "linux_ruleset",
    2: "window_ruleset",
    3: "genian_ruleset",
    4: "fortigate_ruleset"
}

# detected log 인덱스 이름 매핑
detected_log_mapping = {
    1: "linux_detected_log",
    2: "window_detected_log",
    3: "genian_detected_log",
    4: "fortigate_detected_log"
}
```

### 2. input_ruleset.py
사용자로부터 룰셋을 입력받음
1. 프러퍼티 ex : massage, programname
2. 벨류 ex : Starting sysstat-collect.service - system activity accounting tool..., systemd
3. 추가 : 프러퍼티를 추가하겠습니까? y -> 1번으로 다시 가 쿼리 추가 n -> 디텍터 생성

### 3. detector.py
지속적으로 룰셋 기반 로그를 탐지함
linux + window + genian + fortigate 하나로 통합된 버전 추후 생성

---
### test rule-set curl
```sh
curl -X POST "http://3.35.81.217:9200/ruleset/_doc1" -H "Content-Type: application/json" -d '{
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
}'

curl -X POST "http://3.35.81.217:9200/genian_ruleset/_doc" -H "Content-Type: application/json" -d '{
  "name": "Detect Report Auto Generation",
  "system": "linux",
  "query": {
    "query": {
      "bool": {
        "must": [
          {
            "match_phrase": {
              "msg": "리포트 자동생성됨."
            }
          }
        ]
      }
    }
  },
  "severity": 2
}'

'

curl -X POST "http://3.35.81.217:9200/fortigate_ruleset/_doc" -H "Content-Type: application/json" -d '{
    "name": "Detect Fortigate Traffic Close Notice",
    "system": "fortigate",
    "query": {
        "query": {
            "bool": {
                "must": [
                    {
                        "match": {
                            "type": "traffic"
                        }
                    },
                    {
                        "match": {
                            "level": "notice"
                        }
                    },
                    {
                        "match": {
                            "action": "close"
                        }
                    }
                ]
            }
        }
    },
    "severity": 2
}'
```