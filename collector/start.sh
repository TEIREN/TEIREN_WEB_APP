#!/bin/bash
# start.sh
# chmod +x start.sh

sudo apt update
sudo apt install -y python3-venv

VENV_DIR=venv

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv $VENV_DIR
fi

source $VENV_DIR/bin/activate

pip install -r requirements.txt

nohup $VENV_DIR/bin/uvicorn elasticsearch_fastapi:app --host 0.0.0.0 --port 8088 &

deactivate
