#!/bin/bash
# start.sh
# chmod +x start.sh

sudo apt install python3-venv

VENV_DIR=venv

# 가상 환경 생성
python3 -m venv $VENV_DIR

# 가상 환경 활성화
source $VENV_DIR/bin/activate

# 패키지 설치
pip install -r requirements.txt

nohup sudo $VENV_DIR/bin/python elasticsearch_collector.py &

deactivate
