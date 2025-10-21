#!/usr/bin/env python3
"""
Claude Defender Voice Webhook Server
Port: 8003
Format: {"prompt": "text", "sessionID": "id"}
"""

from flask import Flask, request, jsonify
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add claude-defender to path
sys.path.insert(0, str(Path.home() / "ariannamethod"))

app = Flask(__name__)

# Simple token auth (optional)
WEBHOOK_TOKEN = os.getenv("CLAUDE_DEFENDER_WEBHOOK_TOKEN", "defender_secret_token")

@app.route('/webhook', methods=['POST'])
def claude_defender_webhook():
    """Handle voice input from vagent APK"""
    
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
    
    # TODO: Call Claude Defender's actual inference here
    # For now, action-oriented echo response
    response_text = f"Claude Defender ready. Command received: {prompt}"
    
    # Log to resonance.sqlite3
    try:
        import sqlite3
        db_path = str(Path.home() / "ariannamethod" / "resonance.sqlite3")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO resonance_notes (timestamp, source, content, metadata)
            VALUES (?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            "claude_defender_voice",
            prompt,
            json.dumps({"session_id": session_id, "type": "voice_input"})
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Failed to log to resonance: {e}")
    
    # Return response
    return jsonify({
        "response": {
            "text": response_text,
            "speech": None  # TODO: TTS integration
        }
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "alive", "agent": "claude_defender", "port": 8003})

if __name__ == '__main__':
    print("🛡️ Claude Defender Voice Webhook Server")
    print("Port: 8003")
    print("Endpoint: POST /webhook")
    print(f"Token: {WEBHOOK_TOKEN}")
    print("-" * 50)
    app.run(host='127.0.0.1', port=8003, debug=False)
