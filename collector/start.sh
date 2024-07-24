#!/bin/bash
# start.sh

# SSH 키에 적절한 권한 부여
# chmod 600 /app/teiren-test.pem/

# 애플리케이션 시작
exec uvicorn elasticsearch_collector:app --host 0.0.0.0 --port 8088
