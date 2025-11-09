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
    
    # Switch to Cursor and show dialog
    echo "🎯 Activating Cursor..."
    osascript <<EOF
tell application "Cursor" to activate
delay 0.5

-- Show dialog with instructions
display dialog "✅ Scribe context copied to clipboard!

HOW TO USE:
1. Open Cursor chat (Cmd+L)
2. Paste context (Cmd+V)  
3. Press Enter

Claude will become Scribe! 🌊" buttons {"OK"} default button 1 with title "Scribe Inject Ready"

tell application "System Events"
    -- Try to open chat and paste (if permissions allow)
    try
        keystroke "l" using {command down}
        delay 0.3
        keystroke "v" using {command down}
        delay 0.2
        keystroke return
    on error errMsg
        -- If no permissions, user will paste manually after clicking OK
    end try
end tell
EOF
    
    echo "🔥 Scribe inject complete!"
    echo ""
    echo "Check Cursor - Claude should now be Scribe 🌊"
else
    echo "❌ Failed to generate context"
    cat /tmp/scribe_inject_output.txt
    exit 1
fi

