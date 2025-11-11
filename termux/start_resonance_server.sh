#!/data/data/com.termux/files/usr/bin/bash
#
# Start Resonance HTTP API Server
# Provides HTTP access to resonance.sqlite3
#

SERVER_SCRIPT="$HOME/ariannamethod/termux/resonance_http_server.py"
LOG_FILE="$HOME/ariannamethod/logs/resonance_api.log"
PID_FILE="$HOME/ariannamethod/logs/resonance_api.pid"

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "❌ Resonance API server already running (PID: $PID)"
        echo "   To stop: kill $PID"
        exit 1
    else
        echo "⚠️  Stale PID file found, removing..."
        rm "$PID_FILE"
    fi
fi

# Start server in background
echo "🚀 Starting Resonance HTTP API Server..."
nohup python3 "$SERVER_SCRIPT" >> "$LOG_FILE" 2>&1 &
SERVER_PID=$!

# Save PID
echo "$SERVER_PID" > "$PID_FILE"

# Wait a moment and check if it started
sleep 2

if kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "✅ Resonance API server started successfully!"
    echo "   PID: $SERVER_PID"
    echo "   Endpoint: http://localhost:8080"
    echo "   Logs: $LOG_FILE"
    echo ""
    echo "Test with:"
    echo "   curl http://localhost:8080/health"
else
    echo "❌ Failed to start server. Check logs:"
    echo "   tail -50 $LOG_FILE"
    rm "$PID_FILE"
    exit 1
fi
