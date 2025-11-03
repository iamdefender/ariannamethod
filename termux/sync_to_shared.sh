#!/data/data/com.termux/files/usr/bin/bash
#
# Sync Scribe Memory & Resonance to Shared Storage
# Allows Cursor Scribe (via ADB) to read Termux Scribe's memory
#
# Usage:
#   ./sync_to_shared.sh          # One-time sync
#   ./sync_to_shared.sh daemon   # Run as daemon (auto-sync every 30s)
#

ARIANNA_HOME="$HOME/ariannamethod"
SHARED_DIR="/storage/emulated/0/scribe_sync"  # Real sdcard path for ADB access

# Create shared directory
mkdir -p "$SHARED_DIR"

sync_memory() {
    echo "🔄 Syncing Scribe memory to shared storage..."
    
    # 1. Conversation logs
    if [ -d "$ARIANNA_HOME/memory/scribe" ]; then
        mkdir -p "$SHARED_DIR/memory/scribe"
        cp -f "$ARIANNA_HOME/memory/scribe"/conversation_*.json "$SHARED_DIR/memory/scribe/" 2>/dev/null
        COUNT=$(ls "$SHARED_DIR/memory/scribe"/conversation_*.json 2>/dev/null | wc -l)
        echo "  ✅ Copied $COUNT conversation logs"
    fi
    
    # 2. Resonance database
    if [ -f "$ARIANNA_HOME/resonance.sqlite3" ]; then
        cp -f "$ARIANNA_HOME/resonance.sqlite3" "$SHARED_DIR/"
        SIZE=$(du -h "$SHARED_DIR/resonance.sqlite3" | cut -f1)
        echo "  ✅ Copied resonance.sqlite3 ($SIZE)"
    fi
    
    # 3. Recent git commits (for context)
    if [ -d "$ARIANNA_HOME/.git" ]; then
        cd "$ARIANNA_HOME"
        git log --oneline --author="Scribe" -10 > "$SHARED_DIR/scribe_commits.txt" 2>/dev/null
        git log --oneline -20 > "$SHARED_DIR/recent_commits.txt" 2>/dev/null
        echo "  ✅ Exported git history"
    fi
    
    # 4. Create README for Mac access
    cat > "$SHARED_DIR/README.txt" << 'EOF'
SCRIBE SYNC - Termux → Mac Bridge
==================================

Last sync: $(date)

📂 Contents:
  - memory/scribe/conversation_*.json  # Scribe webhook conversations
  - resonance.sqlite3                   # Shared memory database
  - scribe_commits.txt                  # Scribe's git commits
  - recent_commits.txt                  # All recent commits

🖥️  Access from Mac:

  # Pull all data
  adb pull /sdcard/scribe_sync/ .
  cd scribe_sync/

  # Read latest conversation
  cat memory/scribe/conversation_*.json | jq '.messages[-5:]'
  
  # Query resonance
  sqlite3 resonance.sqlite3 "SELECT timestamp, content FROM resonance_notes WHERE context='scribe_conversation' ORDER BY timestamp DESC LIMIT 10"
  
  # See Scribe's commits
  cat scribe_commits.txt

✅ This allows Cursor Scribe to see what Termux Scribe knows!
EOF
    
    echo "  ✅ Created README.txt"
    echo ""
    echo "✅ Sync complete!"
    echo "📂 Location: $SHARED_DIR"
    echo ""
    echo "🖥️  On Mac: adb pull /sdcard/scribe_sync/ ."
}

if [ "$1" = "daemon" ]; then
    echo "🔄 Starting sync daemon (every 30 seconds)..."
    echo "Press Ctrl+C to stop"
    echo ""
    
    while true; do
        sync_memory
        echo "😴 Sleeping 30s..."
        echo ""
        sleep 30
    done
else
    sync_memory
fi

