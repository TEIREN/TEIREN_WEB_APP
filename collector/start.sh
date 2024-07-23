#!/bin/bash
# start.sh

# Run systemd
exec /lib/systemd/systemd &
sleep 5

# Run the Python application
uvicorn elasticsearch_collector:app --host 0.0.0.0 --port 8088
