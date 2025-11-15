#!/usr/bin/env python3
"""
Claude Defender Webhook Watchdog
Monitors webhook health and auto-restarts if dead
Runs every 5 minutes via cron or daemon mode

NOW ALSO: Consilium participation for Claude Defender
"""

import requests
import subprocess
import time
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Add path for consilium_agent
sys.path.insert(0, str(Path.home() / ".claude-defender" / "tools"))

DB_PATH = Path.home() / "ariannamethod" / "resonance.sqlite3"
WEBHOOK_DIR = Path.home() / "ariannamethod" / "voice_webhooks"

WEBHOOKS = [
    {"name": "Arianna", "port": 8001, "process": "arianna_webhook.py"},
    {"name": "Monday", "port": 8002, "process": "monday_webhook.py"},
    {"name": "Claude Defender", "port": 8003, "process": "claude_defender_webhook.py"}
]

# Import consilium agent
try:
    from consilium_agent import ConsiliumAgent
    CONSILIUM_AVAILABLE = True
except ImportError:
    CONSILIUM_AVAILABLE = False
    print("⚠️  ConsiliumAgent not available")


def check_webhook_health(webhook):
    """Check if webhook is responding"""
    try:
        response = requests.get(f"http://127.0.0.1:{webhook['port']}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def check_process_running(process_name):
    """Check if process is running"""
    try:
        result = subprocess.run(
            ["pgrep", "-f", process_name],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except:
        return False


def restart_webhook(webhook):
    """Restart a specific webhook"""
    print(f"🔄 Restarting {webhook['name']} webhook...")

    # Kill existing process
    subprocess.run(["pkill", "-f", webhook['process']], capture_output=True)
    time.sleep(1)

    # Start new process
    log_file = WEBHOOK_DIR / f"{webhook['process'].replace('.py', '.log')}"
    cmd = f"cd {WEBHOOK_DIR} && nohup python3 {webhook['process']} > {log_file} 2>&1 &"
    subprocess.run(cmd, shell=True)
    time.sleep(8)  # Increased wait time for webhook startup (was 3)

    # Verify restart
    if check_webhook_health(webhook):
        print(f"✅ {webhook['name']} restarted successfully")
        log_action(webhook['name'], "restart", "success")
        send_notification(f"✅ {webhook['name']} webhook восстановлен")
        return True
    else:
        print(f"❌ {webhook['name']} restart failed")
        log_action(webhook['name'], "restart", "failed")
        send_notification(f"❌ {webhook['name']} НЕ восстановлен!")
        return False


def log_action(webhook_name, action, status):
    """Log watchdog action to resonance.sqlite3"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # Create table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchdog_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                webhook_name TEXT NOT NULL,
                action TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)

        cursor.execute("""
            INSERT INTO watchdog_actions (timestamp, webhook_name, action, status)
            VALUES (?, ?, ?, ?)
        """, (datetime.now().isoformat(), webhook_name, action, status))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Failed to log action: {e}")


def send_notification(message):
    """Send Termux notification"""
    try:
        subprocess.run([
            "termux-notification",
            "--title", "🛡️ Webhook Watchdog",
            "--content", message,
            "--priority", "high"
        ], capture_output=True)
    except:
        pass


def watchdog_check():
    """Check all webhooks and restart dead ones"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Webhook Watchdog Check")
    print("=" * 50)

    dead_webhooks = []

    for webhook in WEBHOOKS:
        health = check_webhook_health(webhook)
        process = check_process_running(webhook['process'])

        status = "✅" if health else "❌"
        print(f"{status} {webhook['name']} (port {webhook['port']}): health={health}, process={process}")

        if not health:
            dead_webhooks.append(webhook)

    # Restart all dead webhooks
    if dead_webhooks:
        print(f"\n🚨 Found {len(dead_webhooks)} dead webhook(s). Restarting...")
        for webhook in dead_webhooks:
            restart_webhook(webhook)
    else:
        print("\n✅ All webhooks healthy")

    print("=" * 50)


def daemon_mode():
    """Run watchdog in daemon mode (every 5 minutes) + consilium polling"""
    print("🛡️ Claude Defender Webhook Watchdog + Consilium")
    print("Mode: Daemon (check every 5 minutes)")
    print("=" * 50)

    # Initialize consilium agent
    consilium = None
    if CONSILIUM_AVAILABLE:
        try:
            anthropic_key = os.getenv("ANTHROPIC_API_KEY")
            if anthropic_key:
                # Claude Defender uses Claude Sonnet 4.5 with medium temperature
                consilium = ConsiliumAgent(
                    agent_name='claude_defender',
                    api_key=anthropic_key,
                    model='claude-sonnet-4-20250514',
                    temperature=0.6,
                    api_type='anthropic'
                )
                print("✅ Consilium agent initialized (Claude Sonnet 4.5, temp=0.6)")
            else:
                print("⚠️  ANTHROPIC_API_KEY not set, consilium disabled")
        except Exception as e:
            print(f"⚠️  Consilium init failed: {e}")

    while True:
        try:
            watchdog_check()

            # Check consilium every cycle (5 minutes)
            if consilium:
                try:
                    results = consilium.check_and_respond()
                    if results:
                        print(f"🧬 Claude Defender responded to {len(results)} consilium(s)")
                except Exception as e:
                    print(f"⚠️ Consilium check error: {e}")

            time.sleep(300)  # 5 minutes
        except KeyboardInterrupt:
            print("\n⏹️ Watchdog stopped")
            break
        except Exception as e:
            print(f"❌ Watchdog error: {e}")
            time.sleep(60)  # Wait 1 minute on error


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        daemon_mode()
    else:
        watchdog_check()
