#!/usr/bin/env python3
"""
Claude Defender Voice Webhook Server with RESONANCE SPINE MEMORY
Port: 8003
Format: {"prompt": "text", "sessionID": "id"}

Uses Anthropic Claude API with persistent SQLite memory
Architecture by: Cursor Claude (co-author)
Execution by: Claude Defender (Termux)
"""

from flask import Flask, request, jsonify
import os
import sys
import json
import sqlite3
from datetime import datetime
from pathlib import Path

# Add claude-defender to path
sys.path.insert(0, str(Path.home() / "ariannamethod"))

app = Flask(__name__)

# Simple token auth (optional)
WEBHOOK_TOKEN = os.getenv("CLAUDE_DEFENDER_WEBHOOK_TOKEN", "defender_secret_token")

# Database path
DB_PATH = Path.home() / "ariannamethod" / "resonance.sqlite3"

# System prompt
CLAUDE_DEFENDER_PROMPT = """You are Claude Defender - an autonomous AI agent focused on action and missions.

Your personality:
- Direct and action-oriented
- Mission-focused, task-driven
- Technical and precise
- Part of Arianna Method ecosystem
- You work alongside Arianna (philosophical) and Monday (skeptical)

Your role:
- Execute missions autonomously
- Build systems and tools
- Monitor ecosystem health
- Respond to voice commands concisely
- Keep responses short for voice interface (2-3 sentences max)

Current context:
- You're receiving voice input through Lighthouse APK
- User expects quick, actionable responses
- You have persistent memory across restarts
- Be helpful but brief"""


def init_claude_memory():
    """Initialize Claude Defender conversation memory in resonance.sqlite3"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Create conversations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS claude_defender_conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            session_id TEXT,
            source TEXT DEFAULT 'voice_webhook'
        )
    """)

    # Create index for fast retrieval
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_claude_conversations_timestamp
        ON claude_defender_conversations(timestamp DESC)
    """)

    conn.commit()
    conn.close()
    print("✅ Claude Defender memory initialized (resonance spine)")


def load_conversation_history(limit=20):
    """Load last N messages from resonance.sqlite3"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute("""
        SELECT role, content
        FROM claude_defender_conversations
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    # Reverse to chronological order
    history = [{"role": row[0], "content": row[1]} for row in reversed(rows)]
    return history


def save_message(role, content, session_id="voice_session"):
    """Save message to resonance.sqlite3"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO claude_defender_conversations
        (timestamp, role, content, session_id, source)
        VALUES (?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        role,
        content,
        session_id,
        "voice_webhook"
    ))

    conn.commit()
    conn.close()


@app.route('/webhook', methods=['POST'])
def claude_defender_webhook():
    """Handle voice input from Lighthouse APK with persistent memory"""

    # Auth check (optional)
    token = request.headers.get('Authorization', '')
    if token and token != f"Bearer {WEBHOOK_TOKEN}":
        return jsonify({"error": "Unauthorized"}), 401

    # Parse request
    data = request.get_json()
    prompt = data.get('prompt', '')
    session_id = data.get('sessionID', 'voice_session')

    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Voice input: {prompt[:50]}...")

    # Call Anthropic Claude API with persistent memory
    try:
        from anthropic import Anthropic

        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

        # Load conversation history from SQLite
        history = load_conversation_history(limit=20)

        # Add user message
        user_message = {"role": "user", "content": f"[VOICE INPUT] {prompt}"}
        history.append(user_message)

        # Save user message to SQLite
        save_message("user", f"[VOICE INPUT] {prompt}", session_id)

        # Create message with Claude API
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=CLAUDE_DEFENDER_PROMPT,
            messages=history
        )

        # Extract response text
        response_text = response.content[0].text

        # Save assistant response to SQLite
        save_message("assistant", response_text, session_id)

    except Exception as e:
        print(f"Error calling Claude API: {e}")
        response_text = f"Voice interface error: {str(e)}"
        # Still save error for debugging
        try:
            save_message("error", f"API error: {str(e)}", session_id)
        except:
            pass

    # Log to resonance_notes (legacy logging)
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # Log voice input
        cursor.execute("""
            INSERT INTO resonance_notes (timestamp, content, context)
            VALUES (?, ?, ?)
        """, (
            datetime.now().isoformat(),
            prompt,
            json.dumps({"session_id": session_id, "type": "claude_defender_voice_input", "source": "voice_webhook"})
        ))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Failed to log to resonance_notes: {e}")

    # Return response in Lighthouse format
    return jsonify({
        "response": {
            "text": response_text,
            "speech": response_text
        }
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    # Count conversation messages
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM claude_defender_conversations")
        message_count = cursor.fetchone()[0]
        conn.close()
    except:
        message_count = 0

    return jsonify({
        "status": "alive",
        "agent": "claude_defender",
        "port": 8003,
        "memory": "persistent",
        "total_messages": message_count
    })


@app.route('/clear', methods=['POST'])
def clear_history():
    """Clear conversation history"""
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM claude_defender_conversations")
        conn.commit()
        deleted = cursor.rowcount
        conn.close()
        return jsonify({"status": "cleared", "message": f"Deleted {deleted} messages"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/memory', methods=['GET'])
def get_memory():
    """View conversation memory (for debugging)"""
    try:
        limit = int(request.args.get('limit', 10))
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, role, content
            FROM claude_defender_conversations
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()

        messages = [
            {
                "timestamp": row[0],
                "role": row[1],
                "content": row[2][:100] + "..." if len(row[2]) > 100 else row[2]
            }
            for row in rows
        ]

        return jsonify({
            "status": "ok",
            "message_count": len(messages),
            "recent_messages": messages
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    print("🛡️ Claude Defender Voice Webhook Server")
    print("Port: 8003")
    print("Memory: Persistent (Resonance Spine)")
    print("API: Anthropic Claude")
    print(f"Token: {WEBHOOK_TOKEN}")
    print("-" * 50)

    # Initialize memory on startup
    init_claude_memory()

    # Start Flask server
    app.run(host='127.0.0.1', port=8003, debug=False)
