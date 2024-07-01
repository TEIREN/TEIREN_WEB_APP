import json
import time
import logging
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
        res = es.search(index=ruleset_index, body={"query": {"match_all": {}}})
        rulesets = res['hits']['hits']

        logger.info(f"Found {len(rulesets)} rulesets in {ruleset_index}")

        for rule in rulesets:
            rule_query = rule["_source"]["query"]
            severity = rule["_source"]["severity"]
            rule_name = rule["_source"]["name"]
            rule_type = rule["_source"].get("rule_type", "custom")  # Default to 'custom' if not present

            logger.info(f"Applying rule: {rule_name}, Query: {json.dumps(rule_query, indent=4)}")

            # 페이지네이션 설정
            size = 10000
            scroll = '2m'
            try:
                result = es.search(index=log_index_name, body={"query": rule_query["query"]}, scroll=scroll, size=size)
            except Exception as e:
                logger.error(f"Search query failed: {e}")
                continue

            sid = result.get('_scroll_id', None)
            scroll_size = len(result['hits']['hits'])

            if scroll_size == 0:
                logger.info(f"No logs found for rule: {rule_name}")
                continue

            logger.info(f"Found {scroll_size} logs for rule: {rule_name}")

            while scroll_size > 0:
                logger.info(f"Scrolling through {scroll_size} logs for rule: {rule_name}")

                for log in result['hits']['hits']:
                    log_id = log["_id"]
                    log_doc = log["_source"]

                    # 로그 아이디를 룰셋 이름과 결합하여 중복 체크
                    unique_log_id = f"{log_id}_{rule_name}"

                    log_doc["detected_by_rule"] = [rule_name]
                    log_doc["severity"] = severity
                    log_doc["rule_type"] = rule_type  # Add rule_type to the detected log

                    try:
                        es.get(index=detected_log_index, id=unique_log_id)
                        logger.info(f"Log with id {unique_log_id} already exists in {detected_log_index}")
                    except NotFoundError:
                        # Try inserting the log and log the response
                        try:
                            response = es.index(index=detected_log_index, id=unique_log_id, body=log_doc)
                            logger.info(f"Indexed log with id {unique_log_id} into {detected_log_index}")
                        except Exception as e:
                            logger.error(f"Failed to index log with id {unique_log_id}: {e}")
                            logger.error(f"Log document: {json.dumps(log_doc, indent=4)}")

                try:
                    result = es.scroll(scroll_id=sid, scroll=scroll)
                    sid = result.get('_scroll_id', None)
                    scroll_size = len(result['hits']['hits'])
                except Exception as e:
                    logger.error(f"Scrolling failed: {e}")
                    break

            if sid:
                try:
                    es.clear_scroll(scroll_id=sid)
                except Exception as e:
                    logger.error(f"Clearing scroll failed: {e}")

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
    system = "linux"  # 또는 "linux", "genian", "fortigate" 중 하나를 선택
    run_detector(system)
