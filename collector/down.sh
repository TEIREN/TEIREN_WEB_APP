# chmod +x down.sh

sudo rm -f nohup.out

PIDS=$(ps aux | grep 'elasticsearch_fastapi:app --host 0.0.0.0 --port 8088' | grep -v 'grep' | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo "not found"
else
    echo "Stopping elasticsearch_collector.py"
    for PID in $PIDS; do
        sudo kill $PID
        if ps -p $PID > /dev/null; then
            echo "Process $PID did not terminate, sending SIGKILL"
            sudo kill -9 $PID
        else
            echo "Stopped process with PID: $PID"
        fi
    done
fi
