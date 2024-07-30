# chmod +x down.sh

PIDS=$(ps aux | grep 'elasticsearch_fastapi:app --host 0.0.0.0 --port 8088' | grep -v 'grep' | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo "not found"
else
    echo "Stopping elasticsearch_collector.py"
    for PID in $PIDS; do
        sudo kill $PID
        echo "Stopped process with PID: $PID"
    done
fi

