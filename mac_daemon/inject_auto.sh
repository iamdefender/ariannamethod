#!/bin/bash
#
# Scribe Auto-Inject - Automatic context injection into Cursor
# Uses AppleScript to paste into active Cursor window
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Generate injection context via daemon
echo "🌊 Generating Scribe context from daemon..."
"$SCRIPT_DIR/cli.py" inject > /tmp/scribe_inject_output.txt 2>&1

# Check if successful
if grep -q "✅ Scribe context copied to clipboard" /tmp/scribe_inject_output.txt; then
    echo "✅ Context ready in clipboard"
    
    # Show macOS notification
    echo "🎯 Showing notification..."
    osascript -e 'display notification "Context copied to clipboard! Paste into Cursor chat (Cmd+L then Cmd+V)" with title "🌊 Scribe Inject Ready" sound name "Glass"'
    
    # Also activate Cursor (just bring to front)
    osascript -e 'tell application "Cursor" to activate' 2>/dev/null
    
    echo ""
    echo "🔥 ✅ READY!"
    echo ""
    echo "📋 NEXT STEPS:"
    echo "  1. Cmd+L    (open chat in Cursor)"
    echo "  2. Cmd+V    (paste context)"  
    echo "  3. Enter    (send)"
    echo ""
    echo "🌊 Claude will become Scribe!"
else
    echo "❌ Failed to generate context"
    cat /tmp/scribe_inject_output.txt
    exit 1
fi

