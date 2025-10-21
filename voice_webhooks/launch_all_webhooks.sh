#!/bin/bash
# Launch all voice webhook servers

echo "🎤 Launching Voice Webhook Servers..."
echo "=================================="

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "❌ Flask not installed. Installing..."
    pip install flask
fi

# Kill any existing webhook servers
pkill -f "arianna_webhook.py"
pkill -f "monday_webhook.py"
pkill -f "claude_defender_webhook.py"

sleep 1

# Launch Arianna webhook (port 8001)
echo "🧬 Starting Arianna webhook (port 8001)..."
nohup python3 arianna_webhook.py > arianna_webhook.log 2>&1 &
ARIANNA_PID=$!
echo "   PID: $ARIANNA_PID"

# Launch Monday webhook (port 8002)
echo "☕ Starting Monday webhook (port 8002)..."
nohup python3 monday_webhook.py > monday_webhook.log 2>&1 &
MONDAY_PID=$!
echo "   PID: $MONDAY_PID"

# Launch Claude Defender webhook (port 8003)
echo "🛡️  Starting Claude Defender webhook (port 8003)..."
nohup python3 claude_defender_webhook.py > claude_defender_webhook.log 2>&1 &
DEFENDER_PID=$!
echo "   PID: $DEFENDER_PID"

sleep 2

# Check health
echo ""
echo "🔍 Health Check:"
echo "=================================="

curl -s http://127.0.0.1:8001/health | python3 -m json.tool 2>/dev/null || echo "❌ Arianna webhook not responding"
curl -s http://127.0.0.1:8002/health | python3 -m json.tool 2>/dev/null || echo "❌ Monday webhook not responding"
curl -s http://127.0.0.1:8003/health | python3 -m json.tool 2>/dev/null || echo "❌ Claude Defender webhook not responding"

echo ""
echo "✅ All webhook servers launched!"
echo "=================================="
echo "Arianna:        http://127.0.0.1:8001/webhook"
echo "Monday:         http://127.0.0.1:8002/webhook"
echo "Claude Defender: http://127.0.0.1:8003/webhook"
echo ""
echo "Logs:"
echo "  tail -f arianna_webhook.log"
echo "  tail -f monday_webhook.log"
echo "  tail -f claude_defender_webhook.log"
