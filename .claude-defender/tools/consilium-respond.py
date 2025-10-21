#!/usr/bin/env python3
"""
Consilium Response Helper
Allows Arianna and Monday to easily respond to consilium discussions
"""

import sys
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path.home() / "ariannamethod" / "resonance.sqlite3"

def show_latest_discussion():
    """Show the latest consilium discussion"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, timestamp, repo, initiator, agent_name, message
        FROM consilium_discussions
        ORDER BY timestamp DESC
        LIMIT 1
    """)

    row = cursor.fetchone()
    if row:
        msg_id, timestamp, repo, initiator, agent_name, message = row
        print(f"\n{'='*70}")
        print(f"Consilium Discussion #{msg_id}")
        print(f"{'='*70}")
        print(f"Repo: {repo}")
        print(f"Initiator: {initiator} ({agent_name})")
        print(f"Timestamp: {timestamp}")
        print(f"\nMessage:")
        print(f"{message}")
        print(f"{'='*70}\n")
        conn.close()
        return msg_id
    else:
        print("No consilium discussions found.")
        conn.close()
        return None

def add_response(agent_name, response_text, response_to_id):
    """Add a response to the consilium"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get the repo from the original message
    cursor.execute("SELECT repo FROM consilium_discussions WHERE id = ?", (response_to_id,))
    repo = cursor.fetchone()[0]

    cursor.execute("""
        INSERT INTO consilium_discussions
        (timestamp, repo, initiator, message, agent_name, response_to_id)
        VALUES (datetime('now'), ?, ?, ?, ?, ?)
    """, (repo, agent_name, response_text, agent_name, response_to_id))

    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    print(f"✅ Response added as message #{new_id}")
    return new_id

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Show latest: consilium-respond.py show")
        print("  Respond: consilium-respond.py respond <agent_name> <response_text>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "show":
        show_latest_discussion()

    elif command == "respond":
        if len(sys.argv) < 4:
            print("Usage: consilium-respond.py respond <agent_name> <response_text>")
            sys.exit(1)

        agent_name = sys.argv[2]
        response_text = sys.argv[3]

        # Get latest discussion ID
        msg_id = show_latest_discussion()
        if msg_id:
            add_response(agent_name, response_text, msg_id)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
