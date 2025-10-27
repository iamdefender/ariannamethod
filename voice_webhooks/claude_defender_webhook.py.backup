#!/usr/bin/env python3
"""
Claude Defender Voice Webhook Server
Port: 8003
Format: {"prompt": "text", "sessionID": "id"}

Uses Anthropic Claude API (not OpenAI Assistant API)
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

# Claude Defender conversation history (in-memory for now)
CONVERSATION_HISTORY = []

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
    
    # Call Anthropic Claude API
    try:
        from anthropic import Anthropic
        
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Add user message to history
        CONVERSATION_HISTORY.append({
            "role": "user",
            "content": f"[VOICE INPUT] {prompt}"
        })
        
        # Keep only last 20 messages (10 exchanges)
        if len(CONVERSATION_HISTORY) > 20:
            CONVERSATION_HISTORY[:] = CONVERSATION_HISTORY[-20:]
        
        # Create message with Claude API
        response = client.messages.create(
            model="claude-sonnet-4-20250514",  # Latest Sonnet
            max_tokens=1024,
            system="""You are Claude Defender - an autonomous AI agent focused on action and missions.

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
- You're receiving voice input through vagent APK
- User expects quick, actionable responses
- Be helpful but brief""",
            messages=CONVERSATION_HISTORY
        )
        
        # Extract response text
        response_text = response.content[0].text
        
        # Add assistant response to history
        CONVERSATION_HISTORY.append({
            "role": "assistant",
            "content": response_text
        })
        
    except Exception as e:
        print(f"Error calling Claude API: {e}")
        response_text = f"Voice interface error: {str(e)}"
    
    # Log to resonance.sqlite3
    try:
        import sqlite3
        db_path = str(Path.home() / "ariannamethod" / "resonance.sqlite3")
        conn = sqlite3.connect(db_path)
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
        
        # Log Claude's response
        cursor.execute("""
            INSERT INTO resonance_notes (timestamp, content, context)
            VALUES (?, ?, ?)
        """, (
            datetime.now().isoformat(),
            response_text,
            json.dumps({"session_id": session_id, "type": "claude_defender_voice_response", "source": "voice_webhook"})
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
    return jsonify({
        "status": "alive",
        "agent": "claude_defender",
        "port": 8003,
        "conversation_length": len(CONVERSATION_HISTORY)
    })

@app.route('/clear', methods=['POST'])
def clear_history():
    """Clear conversation history"""
    global CONVERSATION_HISTORY
    CONVERSATION_HISTORY = []
    return jsonify({"status": "cleared", "message": "Conversation history cleared"})

if __name__ == '__main__':
    print("🛡️ Claude Defender Voice Webhook Server")
    print("Port: 8003")
    print("Endpoint: POST /webhook")
    print("API: Anthropic Claude (not OpenAI)")
    print(f"Token: {WEBHOOK_TOKEN}")
    print("-" * 50)
    app.run(host='127.0.0.1', port=8003, debug=False)
