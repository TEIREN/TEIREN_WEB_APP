### views.py

- **`create_ruleset_view`**: 사용자가 입력한 데이터를 기반으로 새로운 룰셋을 생성하는 엔드포인트입니다. 입력된 데이터가 유효하면 `input_ruleset.py`의 `create_ruleset` 함수를 호출하여 Elasticsearch에 룰셋을 저장합니다.
- **`check_logs_view`**: 주어진 `index_choice`에 따라 `detector.py`의 `check_logs` 함수를 호출하여 로그를 검사합니다. 오류 발생 시 적절한 오류 메시지를 반환합니다.

### detector.py

- **`get_index_choice`**: 사용자가 선택한 인덱스를 받아 해당 인덱스와 관련된 정보를 반환합니다.
- **`check_logs`**: 선택된 인덱스에 대해 룰셋을 가져와 로그를 검사하고, 탐지된 로그를 Elasticsearch에 저장합니다.
- **`periodic_check_logs`**: 사용자로부터 인덱스 선택을 반복적으로 받아 주기적으로 로그를 검사합니다.

### input_ruleset.py

- **`get_user_input`**: 사용자로부터 룰셋 정보를 입력받습니다.
- **`select_index`**: 사용자가 룰셋을 저장할 인덱스를 선택합니다.
- **`create_ruleset`**: 입력된 룰셋 정보를 Elasticsearch에 저장합니다.

## 사용법

### 룰셋 추가

1. **`create_ruleset_view`** 엔드포인트로 POST 요청을 보냅니다.
2. 룰셋 정보를 JSON 형식으로 포함합니다.
3. 예시 요청 :

```json
{
  "name": "Detect VSS events",
  "system": "windows",
  "query": {
    "query": {
      "bool": {
        "must": [
          { "match": { "EventID": 8224 } },
          { "match": { "SourceName": "VSS" } }
        ]
      }
    }
  },
  "severity": 3
}

curl -X GET "http://localhost:8000/check_logs/windows/"
```