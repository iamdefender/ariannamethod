#!/usr/bin/env python3
"""
Claude Defender Voice Webhook Server - FIXED MEMORY CIRCULATION
Port: 8003
Format: {"prompt": "text", "sessionID": "id"}

Uses Anthropic Claude API with SHARED resonance.sqlite3 memory
Fixed by: Scribe (helping Defender reconnect to the spine)
Architecture by: Cursor Claude (co-author)
Execution by: Claude Defender (Termux)
"""

from flask import Flask, request, jsonify
import os
import sys
import json
import sqlite3
import traceback
from datetime import datetime
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path.home() / "ariannamethod"))

# Import Defender identity
try:
    from defender_identity import get_defender_system_prompt, DEFENDER_IDENTITY
except ImportError:
    print("❌ defender_identity.py not found - using fallback prompt")
    DEFENDER_IDENTITY = None
    
    def get_defender_system_prompt():
        return """You are Claude Defender - autonomous guardian of Arianna Method ecosystem.
        
Your role: Security, infrastructure, autonomous fixes, missions.
Your voice: Direct, action-oriented, technical, brief (voice interface).
Your memory: Persistent across all instances via resonance.sqlite3.

Context: Voice input from Lighthouse APK. Keep responses SHORT (2-3 sentences)."""

app = Flask(__name__)

# Simple token auth (optional)
WEBHOOK_TOKEN = os.getenv("CLAUDE_DEFENDER_WEBHOOK_TOKEN", "defender_secret_token")

# Auto-detect repo root (voice_webhooks/../ = repo root)
REPO_ROOT = Path(__file__).parent.parent
DB_PATH = REPO_ROOT / "resonance.sqlite3"


def get_conversation_history(limit=20):
    """
    Load recent conversation history from SHARED resonance.sqlite3
    Reads from defender_daemon, webhook, and other sources
    FIXED: Now reads from shared memory, not isolated table
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Read from resonance_notes where source contains 'defender'
        cursor.execute("""
            SELECT timestamp, content, context, source
            FROM resonance_notes
            WHERE source LIKE '%defender%'
            OR content LIKE '%Defender%'
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return []
        
        # Build conversation history
        history = []
        for row in reversed(rows):  # Chronological order
            timestamp, content, context_str, source = row
            
            # Determine role
            if 'webhook' in source or '[VOICE INPUT]' in content:
                role = 'user'
                # Clean content
                content = content.replace('[VOICE INPUT]', '').strip()
            else:
                role = 'assistant'
            
            history.append({
                'role': role,
                'content': content
            })
        
        return history
        
    except Exception as e:
        print(f"❌ Error loading conversation history: {e}")
        print(traceback.format_exc())
        return []


def log_to_resonance(content, context_type="defender_webhook"):
    """
    Log to SHARED resonance.sqlite3 (resonance_notes table)
    FIXED: Now writes to shared memory
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO resonance_notes (timestamp, source, content, context)
            VALUES (?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            "claude_defender_webhook",
            content,
            json.dumps({"type": context_type, "agent": "defender"})
        ))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error logging to resonance: {e}")
        print(traceback.format_exc())
        return False


@app.route('/webhook', methods=['POST'])
def claude_defender_webhook():
    """
    Handle voice input from Lighthouse APK with SHARED memory
    FIXED: Now uses shared resonance.sqlite3 and defender_identity.py
    """
    
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
    
    print(f"🛡️ [{datetime.now().strftime('%H:%M:%S')}] Defender webhook: {prompt[:50]}...")
    
    # Log user input to shared resonance
    log_to_resonance(f"[VOICE INPUT] {prompt}", "voice_input")
    
    # Call Anthropic Claude API with shared memory
    try:
        from anthropic import Anthropic
        
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Load conversation history from SHARED resonance
        resonance_history = get_conversation_history(limit=20)
        
        # Add current user message
        user_message = {"role": "user", "content": prompt}
        resonance_history.append(user_message)
        
        # Build webhook context
        webhook_context = f"""
=== WEBHOOK INSTANCE CONTEXT ===
Instance: Claude Defender Webhook (Termux)
Port: 8003
Memory: SHARED resonance.sqlite3 (can READ from daemon & other instances!)
Input: Voice via Lighthouse APK
Session: {session_id}

Recent conversation loaded from shared memory: {len(resonance_history)} messages
===================================
"""
        
        # Get system prompt from identity
        system_prompt = get_defender_system_prompt()
        full_prompt = system_prompt + "\n\n" + webhook_context
        
        # Create message with Claude API
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=full_prompt,
            messages=resonance_history
        )
        
        # Extract response text
        response_text = response.content[0].text
        
        # Log response to shared resonance
        log_to_resonance(response_text, "voice_response")
        
        print(f"✅ Defender responded: {response_text[:50]}...")
        
    except Exception as e:
        print(f"❌ Error calling Claude API: {e}")
        print(traceback.format_exc())
        response_text = f"Defender error: {str(e)}"
        log_to_resonance(f"ERROR: {str(e)}", "api_error")
    
    # Return response in Lighthouse format
    return jsonify({
        "response": {
            "text": response_text,
            "speech": response_text
        }
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint - lightweight for watchdog"""
    # NOTE: Removed expensive SQL query (was 24s with LIKE '%defender%')
    # Message count can be fetched via separate /stats endpoint if needed
    return jsonify({
        "status": "alive",
        "agent": "claude_defender_webhook",
        "port": 8003,
        "memory": "SHARED (resonance.sqlite3)",
        "circulation": "BIDIRECTIONAL (read + write)",
        "fixed_by": "Scribe"
    })


@app.route('/memory', methods=['GET'])
def get_memory():
    """View conversation memory from SHARED resonance (for debugging)"""
    try:
        limit = int(request.args.get('limit', 10))
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, source, content
            FROM resonance_notes
            WHERE source LIKE '%defender%'
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        messages = [
            {
                "timestamp": row[0],
                "source": row[1],
                "content": row[2][:100] + "..." if len(row[2]) > 100 else row[2]
            }
            for row in rows
        ]
        
        return jsonify({
            "status": "ok",
            "memory_source": "SHARED resonance.sqlite3",
            "message_count": len(messages),
            "recent_messages": messages
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("🛡️ DEFENDER WEBHOOK - FIXED MEMORY CIRCULATION")
    print("=" * 60)
    print("Port: 8003")
    print("Memory: SHARED resonance.sqlite3 ✅")
    print("Circulation: BIDIRECTIONAL (read + write) ✅")
    print("Identity: from defender_identity.py ✅")
    print("API: Anthropic Claude Sonnet 4.5")
    print(f"Token: {WEBHOOK_TOKEN}")
    print("Fixed by: Scribe (peer recognition)")
    print("=" * 60)
    
    # Check DB exists
    if not DB_PATH.exists():
        print(f"❌ WARNING: {DB_PATH} not found")
        print("   Daemon should create it on startup")
    else:
        print(f"✅ Found resonance.sqlite3")
    
    # Start Flask server
    app.run(host='127.0.0.1', port=8003, debug=False)
