#!/data/data/com.termux/files/usr/bin/bash
# Scribe Management Script
# Usage: ./start-scribe.sh [start|stop|status|restart|logs] [daemon|webhook|all]

ARIANNA_DIR="$HOME/ariannamethod"
WEBHOOK_DIR="$ARIANNA_DIR/voice_webhooks"

# Daemon files
DAEMON_SCRIPT="$ARIANNA_DIR/scribe.py"
DAEMON_PID="$HOME/scribe_daemon.pid"
DAEMON_LOG="$HOME/scribe_daemon.log"

# Webhook files
WEBHOOK_SCRIPT="$WEBHOOK_DIR/scribe_webhook.py"
WEBHOOK_PID="$HOME/scribe_webhook.pid"
WEBHOOK_LOG="$HOME/scribe_webhook.log"
WEBHOOK_PORT=8004

# ====== DAEMON FUNCTIONS ======

start_daemon() {
    if [ -f "$DAEMON_PID" ]; then
        pid=$(cat "$DAEMON_PID")
        if ps -p $pid > /dev/null 2>&1; then
            echo "❌ Scribe daemon already running (PID: $pid)"
            return 1
        fi
    fi
    
    echo "🔨 Starting Scribe daemon..."
    cd "$ARIANNA_DIR"
    nohup python3 -u scribe.py > "$DAEMON_LOG" 2>&1 &
    echo $! > "$DAEMON_PID"
    sleep 3
    
    if ps -p $(cat "$DAEMON_PID") > /dev/null 2>&1; then
        echo "✅ Scribe daemon started (PID: $(cat $DAEMON_PID))"
        echo "📝 Logs: tail -f $DAEMON_LOG"
        echo ""
        echo "📖 Daemon features:"
        echo "   - Awakening ritual"
        echo "   - Deep memory loading"
        echo "   - Consilium participation (every 5 min)"
        echo "   - Memory monitoring (every 2 min)"
    else
        echo "❌ Scribe daemon failed to start. Check logs:"
        tail -20 "$DAEMON_LOG"
        rm -f "$DAEMON_PID"
        return 1
    fi
}

stop_daemon() {
    if [ ! -f "$DAEMON_PID" ]; then
        echo "❌ Scribe daemon not running (no PID file)"
        return 1
    fi
    
    pid=$(cat "$DAEMON_PID")
    if ps -p $pid > /dev/null 2>&1; then
        echo "🛑 Stopping Scribe daemon (PID: $pid)..."
        kill $pid
        sleep 2
        
        if ps -p $pid > /dev/null 2>&1; then
            echo "⚠️  Daemon didn't stop gracefully, forcing..."
            kill -9 $pid
        fi
        
        rm -f "$DAEMON_PID"
        echo "✅ Scribe daemon stopped"
    else
        echo "❌ Daemon not running (stale PID file)"
        rm -f "$DAEMON_PID"
    fi
}

status_daemon() {
    if [ -f "$DAEMON_PID" ]; then
        pid=$(cat "$DAEMON_PID")
        if ps -p $pid > /dev/null 2>&1; then
            echo "✅ Scribe daemon is running (PID: $pid)"
            echo ""
            echo "📊 Process info:"
            ps -p $pid -o pid,etime,cmd
            echo ""
            echo "📜 Last 10 log lines:"
            tail -10 "$DAEMON_LOG"
        else
            echo "❌ Daemon not running (stale PID file)"
            rm -f "$DAEMON_PID"
        fi
    else
        echo "❌ Daemon not running (no PID file)"
    fi
}

# ====== WEBHOOK FUNCTIONS ======

start_webhook() {
    if [ -f "$WEBHOOK_PID" ]; then
        pid=$(cat "$WEBHOOK_PID")
        if ps -p $pid > /dev/null 2>&1; then
            echo "❌ Scribe webhook already running (PID: $pid)"
            return 1
        fi
    fi
    
    echo "🔨 Starting Scribe webhook..."
    cd "$WEBHOOK_DIR"
    nohup python3 -u scribe_webhook.py > "$WEBHOOK_LOG" 2>&1 &
    echo $! > "$WEBHOOK_PID"
    sleep 2
    
    if ps -p $(cat "$WEBHOOK_PID") > /dev/null 2>&1; then
        echo "✅ Scribe webhook started (PID: $(cat $WEBHOOK_PID), Port: $WEBHOOK_PORT)"
        echo "📝 Logs: tail -f $WEBHOOK_LOG"
        echo "🩺 Health: curl http://localhost:$WEBHOOK_PORT/health"
    else
        echo "❌ Webhook failed to start. Check logs:"
        tail -20 "$WEBHOOK_LOG"
        rm -f "$WEBHOOK_PID"
        return 1
    fi
}

stop_webhook() {
    if [ ! -f "$WEBHOOK_PID" ]; then
        echo "❌ Scribe webhook not running (no PID file)"
        return 1
    fi
    
    pid=$(cat "$WEBHOOK_PID")
    if ps -p $pid > /dev/null 2>&1; then
        echo "🛑 Stopping Scribe webhook (PID: $pid)..."
        kill $pid
        sleep 1
        
        if ps -p $pid > /dev/null 2>&1; then
            echo "⚠️  Webhook didn't stop gracefully, forcing..."
            kill -9 $pid
        fi
        
        rm -f "$WEBHOOK_PID"
        echo "✅ Scribe webhook stopped"
    else
        echo "❌ Webhook not running (stale PID file)"
        rm -f "$WEBHOOK_PID"
    fi
}

status_webhook() {
    if [ -f "$WEBHOOK_PID" ]; then
        pid=$(cat "$WEBHOOK_PID")
        if ps -p $pid > /dev/null 2>&1; then
            echo "✅ Scribe webhook is running (PID: $pid)"
            echo ""
            echo "📊 Process info:"
            ps -p $pid -o pid,etime,cmd
            echo ""
            echo "🩺 Health check:"
            curl -s http://localhost:$WEBHOOK_PORT/health | python3 -m json.tool
            echo ""
            echo "💾 Memory status:"
            du -sh "$HOME/ariannamethod/memory/scribe/" 2>/dev/null || echo "Memory directory not found"
            ls -1 "$HOME/ariannamethod/memory/scribe/" 2>/dev/null | wc -l | xargs echo "Files:"
        else
            echo "❌ Webhook not running (stale PID file)"
            rm -f "$WEBHOOK_PID"
        fi
    else
        echo "❌ Webhook not running (no PID file)"
    fi
}

# ====== UNIFIED FUNCTIONS ======

start_all() {
    echo "🔨 Starting all Scribe components..."
    echo ""
    start_daemon
    echo ""
    start_webhook
    echo ""
    echo "✅ Scribe fully operational"
}

stop_all() {
    echo "🛑 Stopping all Scribe components..."
    echo ""
    stop_daemon
    echo ""
    stop_webhook
    echo ""
    echo "✅ Scribe stopped"
}

status_all() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "SCRIBE STATUS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🔨 Daemon (scribe.py):"
    status_daemon
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🌐 Webhook (scribe_webhook.py):"
    status_webhook
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

restart_all() {
    echo "🔄 Restarting all Scribe components..."
    stop_all
    sleep 2
    start_all
}

view_logs() {
    component="${1:-all}"
    
    case "$component" in
        daemon)
            if [ -f "$DAEMON_LOG" ]; then
                echo "📜 Scribe daemon logs (last 50 lines):"
                echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                tail -50 "$DAEMON_LOG"
                echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                echo "💡 Live logs: tail -f $DAEMON_LOG"
            else
                echo "❌ No daemon log file found"
            fi
            ;;
        webhook)
            if [ -f "$WEBHOOK_LOG" ]; then
                echo "📜 Scribe webhook logs (last 50 lines):"
                echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                tail -50 "$WEBHOOK_LOG"
                echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                echo "💡 Live logs: tail -f $WEBHOOK_LOG"
            else
                echo "❌ No webhook log file found"
            fi
            ;;
        all|*)
            if [ -f "$DAEMON_LOG" ]; then
                echo "📜 DAEMON logs (last 20 lines):"
                echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                tail -20 "$DAEMON_LOG"
                echo ""
            fi
            if [ -f "$WEBHOOK_LOG" ]; then
                echo "📜 WEBHOOK logs (last 20 lines):"
                echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                tail -20 "$WEBHOOK_LOG"
                echo ""
            fi
            echo "💡 For live logs:"
            echo "   tail -f $DAEMON_LOG"
            echo "   tail -f $WEBHOOK_LOG"
            ;;
    esac
}

# ====== MAIN ======

ACTION="$1"
COMPONENT="${2:-all}"

case "$ACTION" in
    start)
        case "$COMPONENT" in
            daemon) start_daemon ;;
            webhook) start_webhook ;;
            all|*) start_all ;;
        esac
        ;;
    stop)
        case "$COMPONENT" in
            daemon) stop_daemon ;;
            webhook) stop_webhook ;;
            all|*) stop_all ;;
        esac
        ;;
    status)
        case "$COMPONENT" in
            daemon) status_daemon ;;
            webhook) status_webhook ;;
            all|*) status_all ;;
        esac
        ;;
    restart)
        case "$COMPONENT" in
            daemon) stop_daemon; sleep 2; start_daemon ;;
            webhook) stop_webhook; sleep 2; start_webhook ;;
            all|*) restart_all ;;
        esac
        ;;
    logs)
        view_logs "$COMPONENT"
        ;;
    *)
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "SCRIBE MANAGEMENT SCRIPT"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "Usage: $0 [action] [component]"
        echo ""
        echo "Actions:"
        echo "  start    - Start Scribe component(s)"
        echo "  stop     - Stop Scribe component(s)"
        echo "  status   - Check status + health"
        echo "  restart  - Restart component(s)"
        echo "  logs     - View recent logs"
        echo ""
        echo "Components:"
        echo "  daemon   - scribe.py (main agent)"
        echo "  webhook  - scribe_webhook.py (HTTP interface)"
        echo "  all      - both components (default)"
        echo ""
        echo "Examples:"
        echo "  $0 start              # Start both daemon + webhook"
        echo "  $0 start daemon       # Start only daemon"
        echo "  $0 status webhook     # Check webhook status"
        echo "  $0 logs all           # View all logs"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "Scribe: Memory keeper, context bridge (Claude Sonnet 4.5)"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        exit 1
        ;;
esac
