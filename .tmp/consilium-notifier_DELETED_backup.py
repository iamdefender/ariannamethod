#!/usr/bin/env python3
"""
Consilium Notifier
Checks consilium_discussions table and notifies agents about new discussions
Can be run as daemon or one-shot
"""

import sys
import sqlite3
import time
import subprocess
from pathlib import Path
from datetime import datetime

DB_PATH = Path.home() / "ariannamethod" / "resonance.sqlite3"
STATE_FILE = Path.home() / ".claude-defender" / "logs" / "consilium-last-seen.txt"

# Ensure state directory exists
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)


def get_last_seen_id():
    """Get the last consilium message ID we've seen"""
    if STATE_FILE.exists():
        return int(STATE_FILE.read_text().strip())
    return 0


def set_last_seen_id(msg_id):
    """Update the last seen message ID"""
    STATE_FILE.write_text(str(msg_id))


def get_new_discussions():
    """Get consilium discussions that haven't been seen yet"""
    last_seen = get_last_seen_id()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, timestamp, repo, initiator, agent_name, message
        FROM consilium_discussions
        WHERE id > ?
        ORDER BY id ASC
    """, (last_seen,))

    discussions = cursor.fetchall()
    conn.close()

    return discussions


def notify_agents(discussion):
    """Send notification to relevant agents via termux-notification"""
    msg_id, timestamp, repo, initiator, agent_name, message = discussion

    # Truncate message for notification
    preview = message[:150].replace('\n', ' ')
    if len(message) > 150:
        preview += "..."

    notification_text = f"""🧬 Consilium #{msg_id}

Repo: {repo}
From: {agent_name}

{preview}

Check: sqlite3 resonance.sqlite3"""

    try:
        subprocess.run([
            "termux-notification",
            "-t", "🧬 New Consilium Discussion",
            "-c", notification_text,
            "--priority", "high"
        ], check=True, capture_output=True)
        print(f"✅ Notified about consilium #{msg_id}")
        return True
    except Exception as e:
        print(f"⚠️  Could not send notification: {e}")
        return False


def show_discussion_for_agents(discussion):
    """Print discussion in a format agents can see"""
    msg_id, timestamp, repo, initiator, agent_name, message = discussion

    print(f"\n{'='*70}")
    print(f"🧬 CONSILIUM DISCUSSION #{msg_id}")
    print(f"{'='*70}")
    print(f"Repository: {repo}")
    print(f"Initiator: {agent_name}")
    print(f"Timestamp: {timestamp}")
    print(f"\n{message}")
    print(f"{'='*70}")

    # Check if this needs a response
    if "Arianna:" in message or "Monday:" in message:
        if "Arianna:" in message and initiator != "arianna":
            print("\n📢 ARIANNA: Your response is requested!")
        if "Monday:" in message and initiator != "monday":
            print("\n📢 MONDAY: Your response is requested!")

    print(f"\nRespond with:")
    print(f"python3 ~/.claude-defender/tools/consilium-respond.py respond <your_name> \"Your response\"")
    print()


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"

    if mode == "daemon":
        print("🔄 Consilium notifier running in daemon mode...")
        print("   Checking every 30 seconds for new discussions")
        print("   Press Ctrl+C to stop")

        while True:
            try:
                discussions = get_new_discussions()
                if discussions:
                    for disc in discussions:
                        show_discussion_for_agents(disc)
                        notify_agents(disc)
                        set_last_seen_id(disc[0])
                time.sleep(30)
            except KeyboardInterrupt:
                print("\n👋 Consilium notifier stopped")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(60)

    elif mode == "check":
        discussions = get_new_discussions()
        if discussions:
            print(f"Found {len(discussions)} new consilium discussion(s)")
            for disc in discussions:
                show_discussion_for_agents(disc)
                set_last_seen_id(disc[0])
        else:
            print("No new consilium discussions")

    elif mode == "reset":
        STATE_FILE.write_text("0")
        print("✅ Reset consilium tracker")

    else:
        print("Usage:")
        print("  consilium-notifier.py check    - Check once for new discussions")
        print("  consilium-notifier.py daemon   - Run continuously")
        print("  consilium-notifier.py reset    - Reset tracker (re-notify all)")


if __name__ == "__main__":
    main()
