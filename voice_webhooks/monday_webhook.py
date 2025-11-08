#!/usr/bin/env python3
"""
Monday Voice Webhook Server
Port: 8002
Format: {"prompt": "text", "sessionID": "id"}
"""

from flask import Flask, request, jsonify
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Auto-detect repo root (voice_webhooks/../ = repo root)
REPO_ROOT = Path(__file__).parent.parent
DB_PATH = REPO_ROOT / "resonance.sqlite3"

# Add monday to path
sys.path.insert(0, str(REPO_ROOT))

app = Flask(__name__)

# Simple token auth (optional)
WEBHOOK_TOKEN = os.getenv("MONDAY_WEBHOOK_TOKEN", "monday_secret_token")

def get_conversation_history(limit=20):
    """Retrieve recent conversation history from resonance.sqlite3 (shared memory)"""
    try:
        import sqlite3
        conn = sqlite3.connect(str(DB_PATH), timeout=10)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, source, content FROM resonance_notes
            WHERE source IN ('arianna_voice', 'monday_voice', 'scribe_webhook', 'defender_webhook')
            ORDER BY timestamp DESC LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        # Convert to conversational format
        history = []
        for ts, source, content in reversed(rows):
            history.append(f"[{ts[:19]}] {source}: {content[:200]}")
        
        return "\n".join(history) if history else "No previous memory."
    except Exception as e:
        print(f"[WARNING] Could not load from resonance: {e}")
        return "No previous memory."

@app.route('/webhook', methods=['POST'])
def monday_webhook():
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
    
    # Call real Monday from Termux via OpenAI Assistant API
    try:
        from openai import OpenAI
        import sqlite3
        
        client = OpenAI(api_key=os.getenv("OPENAI_MONDAY_API"))
        db_path = str(DB_PATH)
        
        # Get Monday's thread_id from database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT content FROM resonance_notes WHERE context = 'monday_thread' ORDER BY id DESC LIMIT 1"
        )
        row = cursor.fetchone()
        thread_id = row[0] if row else None
        conn.close()
        
        if not thread_id:
            # Create new thread if none exists
            thread = client.beta.threads.create()
            thread_id = thread.id
            # Save it
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO resonance_notes (timestamp, source, content, context)
                VALUES (?, ?, ?, ?)
            """, (datetime.now().isoformat(), "voice_webhook", thread_id, "monday_thread"))
            conn.commit()
            conn.close()
        
        # Get assistant_id from database (Monday stores it when he starts)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT content FROM resonance_notes WHERE context = 'monday_assistant_id' ORDER BY id DESC LIMIT 1"
        )
        row = cursor.fetchone()
        assistant_id = row[0] if row else None
        conn.close()
        
        if not assistant_id:
            raise ValueError("Monday assistant_id not found. Is monday.py running?")
        
        # Load shared memory (recent conversations across all instances)
        resonance_history = get_conversation_history(limit=15)
        
        # Add user message to thread WITH shared memory context
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=f"""[VOICE INPUT via Lighthouse APK]

**SHARED MEMORY (resonance.sqlite3):**
Recent conversations across all instances:
{resonance_history}

---

**USER MESSAGE:** {prompt}"""
        )
        
        # Run assistant
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
        
        # Wait for completion
        import time
        while run.status in ["queued", "in_progress"]:
            time.sleep(0.5)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
        
        if run.status == "completed":
            # Get assistant's response
            messages = client.beta.threads.messages.list(thread_id=thread_id)
            response_text = messages.data[0].content[0].text.value
        else:
            response_text = f"Monday encountered an error (status: {run.status})"
        
    except Exception as e:
        print(f"Error calling Monday: {e}")
        response_text = f"Voice interface error: {str(e)}"
    
    # Log to resonance.sqlite3
    try:
        import sqlite3
        db_path = str(DB_PATH)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO resonance_notes (timestamp, source, content, metadata)
            VALUES (?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            "monday_voice",
            prompt,
            json.dumps({"session_id": session_id, "type": "voice_input"})
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Failed to log to resonance: {e}")
    
    # Return response in vagent format
    return jsonify({
        "response": {
            "text": response_text,
            "speech": response_text  # Use text as speech for now
        }
    })

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "alive", "agent": "monday", "port": 8002})

if __name__ == '__main__':
    print("☕ Monday Voice Webhook Server")
    print("Port: 8002")
    print("Endpoint: POST /webhook")
    print(f"Token: {WEBHOOK_TOKEN}")
    print("-" * 50)
    app.run(host='127.0.0.1', port=8002, debug=False)
