import json
import time
import logging
import threading
from elasticsearch import Elasticsearch, NotFoundError, ConnectionError

# Elasticsearch 클라이언트를 설정합니다.
es = Elasticsearch(hosts=["http://3.35.81.217:9200"])

# Logging 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 인덱스 매핑 설정
log_index = {
    "linux": "test_linux_syslog",
    "window": "test_window_syslog",
    "genian": "test_genian_syslog",
    "fortigate": "test_fortigate_syslog"
}

ruleset_mapping = {
    "linux": "linux_ruleset",
    "window": "window_ruleset",
    "genian": "genian_ruleset",
    "fortigate": "fortigate_ruleset"
}

detected_log_mapping = {
    "linux": "linux_detected_log",
    "window": "window_detected_log",
    "genian": "genian_detected_log",
    "fortigate": "fortigate_detected_log"
}

# Elasticsearch 라이브러리의 디버그 로그를 비활성화
logging.getLogger("elastic_transport.transport").setLevel(logging.CRITICAL)
logging.getLogger("urllib3.connectionpool").setLevel(logging.CRITICAL)

# 사용자 선택에 따라 인덱스 설정
def get_index_choice(system):
    if system not in log_index:
        raise ValueError("Invalid system choice.")
    return {
        'log_index_name': log_index[system],
        'ruleset_index': ruleset_mapping[system],
        'detected_log_index': detected_log_mapping[system]
    }

# 로그 체크 함수
def check_logs(system):
    index_data = get_index_choice(system)
    log_index_name = index_data['log_index_name']
    ruleset_index = index_data['ruleset_index']
    detected_log_index = index_data['detected_log_index']

    try:
        res = es.search(index=ruleset_index, body={"query": {"term": {"status": 1}}})
        rulesets = res['hits']['hits']

        logger.info(f"Found {len(rulesets)} active rulesets in {ruleset_index}")

        def process_rule(rule):
            rule_query = rule["_source"]["query"]
            severity = rule["_source"]["severity"]
            rule_name = rule["_source"]["name"]
            rule_type = rule["_source"].get("rule_type", "custom")  # Default to 'custom' if not present

            logger.info(f"Applying rule: {rule_name}, Query: {json.dumps(rule_query, indent=4)}")

            # 페이지네이션 설정
            size = 1000  # 한번에 가져올 문서 수를 줄임
            scroll = '5m'  # 스크롤 유지 시간을 늘림
            try:
                result = es.search(index=log_index_name, body=rule_query, scroll=scroll, size=size)
            except Exception as e:
                logger.error(f"Search query failed for rule {rule_name}: {e}")
                return

            sid = result.get('_scroll_id', None)
            scroll_size = len(result['hits']['hits'])

            if scroll_size == 0:
                logger.info(f"No logs found for rule: {rule_name}")
                return

            detected_logs_count = 0

            while scroll_size > 0:
                for log in result['hits']['hits']:
                    log_id = log["_id"]
                    log_doc = log["_source"]

                    # 로그 아이디를 룰셋 이름과 결합하여 중복 체크
                    unique_log_id = f"{log_id}_{rule_name}"

                    # 이전에 탐지된 기록이 있는지 확인
                    try:
                        existing_log = es.get(index=detected_log_index, id=unique_log_id)
                        existing_detected_by_rules = existing_log['_source'].get("detected_by_rule", "")
                    except NotFoundError:
                        existing_detected_by_rules = ""

                    if isinstance(existing_detected_by_rules, str):
                        existing_detected_by_rules = existing_detected_by_rules.split(",")
                    elif isinstance(existing_detected_by_rules, list):
                        pass
                    else:
                        existing_detected_by_rules = []

                    detected_by_rules_set = set(filter(None, existing_detected_by_rules))  # 빈 문자열 제거
                    detected_by_rules_set.add(rule_name)

                    log_doc["detected_by_rule"] = ",".join(detected_by_rules_set)
                    log_doc["severity"] = severity
                    log_doc["rule_type"] = rule_type  # Add rule_type to the detected log

                    try:
                        es.index(index=detected_log_index, id=unique_log_id, body=log_doc)
                        detected_logs_count += 1
                    except Exception as e:
                        logger.error(f"Failed to index log with id {unique_log_id}: {e}")

                try:
                    result = es.scroll(scroll_id=sid, scroll=scroll)
                    sid = result.get('_scroll_id', None)
                    scroll_size = len(result['hits']['hits'])
                except NotFoundError as e:
                    logger.error(f"Scrolling failed: {e}")
                    break
                except Exception as e:
                    logger.error(f"An error occurred during scrolling: {e}")
                    break

            if sid:
                try:
                    es.clear_scroll(scroll_id=sid)
                except NotFoundError:
                    logger.warning(f"Scroll ID {sid} not found when clearing scroll")
                except Exception as e:
                    logger.error(f"Clearing scroll failed: {e}")

            logger.info(f"Rule {rule_name} detected {detected_logs_count} logs")

        threads = []
        for rule in rulesets:
            thread = threading.Thread(target=process_rule, args=(rule,))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

    except ConnectionError as e:
        logger.error(f"Connection error: {e}")
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)

# 시스템 선택에 따른 로그 체크 실행
def run_detector(system):
    while True:
        check_logs(system)
        time.sleep(60)  # 60초마다 로그를 체크

if __name__ == "__main__":
    systems = ["linux", "window", "genian", "fortigate"]

    threads = []
    for system in systems:
        thread = threading.Thread(target=run_detector, args=(system,))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()
