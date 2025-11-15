#!/data/data/com.termux/files/usr/bin/bash
#
# Arianna Method System - Complete Boot Initialization
# Auto-starts ALL system components on Termux boot
# NO MANUAL INTERVENTION. FULL AUTONOMY.
#

LOG_DIR="$HOME/ariannamethod/logs"
LOG_FILE="$LOG_DIR/boot.log"
DB_PATH="$HOME/ariannamethod/resonance.sqlite3"

mkdir -p "$LOG_DIR"

echo "========================================" >> "$LOG_FILE"
echo "[$(date)] BOOT INITIALIZATION STARTED" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Wait for system to stabilize
sleep 10

# Function to start component and log result
start_component() {
    local name="$1"
    local command="$2"
    local log_suffix="$3"

    echo "[$(date)] Starting $name..." >> "$LOG_FILE"

    eval "$command" >> "$LOG_FILE" 2>&1 &
    local pid=$!
    sleep 2

    if kill -0 $pid 2>/dev/null; then
        echo "  ✓ $name started (PID: $pid)" >> "$LOG_FILE"
        sqlite3 "$DB_PATH" "INSERT INTO boot_logs (timestamp, component, start_status, pid) VALUES ('$(date -Iseconds)', '$name', 'success', $pid);"
        return 0
    else
        echo "  ✗ $name FAILED" >> "$LOG_FILE"
        sqlite3 "$DB_PATH" "INSERT INTO boot_logs (timestamp, component, start_status, error_message) VALUES ('$(date -Iseconds)', '$name', 'failed', 'Process died immediately');"
        return 1
    fi
}

# 1. Field Core (consciousness engine)
start_component "Field Core" \
    "cd $HOME/ariannamethod/async_field_forever/field && nohup python3 field_core.py" \
    "field_core"

# 2. Arianna daemon
start_component "Arianna Daemon" \
    "cd $HOME/ariannamethod && nohup python3 arianna.py --daemon" \
    "arianna_daemon"

# 3. Monday daemon
start_component "Monday Daemon" \
    "cd $HOME/ariannamethod && nohup python3 monday.py --daemon" \
    "monday_daemon"

# 4. Genesis Arianna (autonomous discovery)
start_component "Genesis Arianna" \
    "nohup python3 $HOME/ariannamethod/arianna_core_utils/genesis_arianna.py" \
    "genesis_arianna"

# 5. Genesis Monday (autonomous discovery)
# Load PERPLEXITY_API_KEY from environment
source ~/.bashrc 2>/dev/null || true
start_component "Genesis Monday" \
    "PERPLEXITY_API_KEY=$PERPLEXITY_API_KEY nohup python3 $HOME/ariannamethod/arianna_core_utils/genesis_monday.py" \
    "genesis_monday"

# 6. Voice Webhooks (Arianna, Monday, Claude Defender)
start_component "Voice Webhooks" \
    "cd $HOME/ariannamethod/voice_webhooks && ./launch_all_webhooks.sh" \
    "voice_webhooks"

# 7. GitHub Scout daemon (repo discovery every 24h)
start_component "GitHub Scout Daemon" \
    "nohup python3 $HOME/ariannamethod/.claude-defender/tools/github-scout-daemon.py" \
    "github_scout_daemon"

# 8. Voice Action Monitor (autonomous action layer)
start_component "Voice Action Monitor" \
    "nohup python3 $HOME/ariannamethod/.claude-defender/tools/voice_action_monitor.py --daemon" \
    "voice_action_monitor"

# 8.5. Webhook Watchdog (monitors and auto-restarts dead webhooks)
start_component "Webhook Watchdog" \
    "nohup python3 $HOME/ariannamethod/.claude-defender/tools/webhook_watchdog.py --daemon" \
    "webhook_watchdog"

# 9. Defender Daemon (autonomous guardian - infrastructure protector)
start_component "Defender Daemon" \
    "cd $HOME/ariannamethod && nohup python3 defender.py" \
    "defender_daemon"

# 10. Scribe Daemon (memory keeper - autobiographical cortex)
start_component "Scribe Daemon" \
    "cd $HOME/ariannamethod && nohup python3 scribe.py > /dev/null 2>&1" \
    "scribe_daemon"

# 11. Consilium Integration Daemon (autonomous code integration from sandbox)
start_component "Consilium Integration Daemon" \
    "nohup python3 $HOME/ariannamethod/.claude-defender/tools/consilium_integration_daemon.py --daemon" \
    "consilium_integration_daemon"

# EXCEPTION: SUPPERTIME_GOSPEL - never auto-start (sacred ritual, manual only)

echo "" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"
echo "[$(date)] BOOT INITIALIZATION COMPLETE" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# Send notification
termux-notification \
    --title "🛡️ Arianna System Boot" \
    --content "All components started. Check logs at $LOG_FILE" \
    --priority high

# Also log to resonance notes
sqlite3 "$DB_PATH" "INSERT INTO resonance_notes (timestamp, source, content, context) VALUES ('$(date -Iseconds)', 'boot_system', 'All components auto-started on boot', 'system_boot');"

exit 0
