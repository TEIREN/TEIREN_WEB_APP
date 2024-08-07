# detector.py
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

# Elasticsearch 라이브러리의 디버그 로그를 비활성화
logging.getLogger("elastic_transport.transport").setLevel(logging.CRITICAL)
logging.getLogger("urllib3.connectionpool").setLevel(logging.CRITICAL)

# 인덱스 매핑 설정 (TAG_NAME 기준으로 동적 설정)
def get_index_choice(system, tag_name=None):
    try:
        if system in ["mysql", "mssql", "fluentd"] and tag_name:
            return {
                'log_index_name': f"{tag_name}_syslog",
                'ruleset_index': f"{tag_name}_ruleset",
                'detected_log_index': f"{tag_name}_detected_log"
            }
        else:
            log_index = {
                "linux": "linux_syslog",
                "windows": "windows_syslog",
                "genian": "genian_syslog",
                "fortigate": "fortigate_syslog"
            }
            ruleset_mapping = {
                "linux": "linux_ruleset",
                "windows": "window_ruleset",
                "genian": "genian_ruleset",
                "fortigate": "fortigate_ruleset"
            }
            detected_log_mapping = {
                "linux": "linux_detected_log",
                "windows": "window_detected_log",
                "genian": "genian_detected_log",
                "fortigate": "fortigate_detected_log"
            }
            if system not in log_index:
                raise ValueError("Invalid system choice.")
            return {
                'log_index_name': log_index[system],
                'ruleset_index': ruleset_mapping[system],
                'detected_log_index': detected_log_mapping[system]
            }
    except Exception as e:
        logger.error(f"Error in get_index_choice: {e}")
        raise

# 로그 체크 함수
def check_logs(system, tag_name=None):
    try:
        index_data = get_index_choice(system, tag_name)
        log_index_name = index_data['log_index_name']
        ruleset_index = index_data['ruleset_index']
        detected_log_index = index_data['detected_log_index']

        # 룰셋을 검색합니다.
        res = es.search(index=ruleset_index, body={"query": {"match_all": {}}})
        rulesets = res['hits']['hits']

        logger.info(f"Found {len(rulesets)} rulesets in {ruleset_index}")

        def process_rule(rule):
            try:
                rule_query = rule["_source"]["query"]
                severity = rule["_source"]["severity"]
                rule_name = rule["_source"]["name"]
                rule_type = rule["_source"].get("rule_type", "custom")  # 기본값을 'custom'으로 설정

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
            except Exception as e:
                logger.error(f"Error in process_rule: {e}")

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
        logger.error(f"An error occurred in check_logs: {e}", exc_info=True)

# 시스템 선택에 따른 로그 체크 실행
def run_detector(system, tag_name=None):
    while True:
        try:
            check_logs(system, tag_name)
            time.sleep(60)  # 60초마다 로그를 체크
        except Exception as e:
            logger.error(f"Error in run_detector: {e}")

# 활성화된 시스템을 가져오는 함수
def get_active_systems():
    try:
        res = es.search(index="integration_info", body={"query": {"term": {"status": "started"}}})
        systems = res['hits']['hits']
        return [(system['_source']['SYSTEM'], system['_source'].get('TAG_NAME')) for system in systems]
    except Exception as e:
        logger.error(f"Error retrieving active systems: {e}")
        return []

if __name__ == "__main__":
    try:
        active_systems = get_active_systems()

        threads = []
        for system, tag_name in active_systems:
            thread = threading.Thread(target=run_detector, args=(system, tag_name))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()
    except Exception as e:
        logger.error(f"Error in main: {e}")
