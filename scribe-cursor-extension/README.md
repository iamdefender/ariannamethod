# 🌊 Scribe - Memory Keeper for Cursor

VS Code/Cursor extension for Mac Daemon integration.

## Features

### Commands (Cmd+Shift+P) + Keyboard Shortcuts
- **Scribe: Inject Identity** (`Alt+Shift+I`) - Generate Scribe context and copy to clipboard
- **Scribe: Show Status** (`Alt+Shift+S`) - Show daemon status (phone, sync, project)
- **Scribe: Sync Memory** (`Alt+Shift+Y`) - Trigger memory sync from Termux
- **Scribe: Remind** (`Alt+Shift+R`) - Search memory (git/code/resonance)
- **Scribe: Open Chat** (`Alt+Shift+C`) - Interactive chat with daemon

### Status Bar
- **🌊 Scribe ✓** - Daemon running, phone connected
- **🌊 Scribe ○** - Daemon running, phone disconnected
- **🌊 Scribe ✗** - Daemon stopped

Click status bar → Show Status

## Installation

### 1. Install Extension

**Option A: From source (recommended)**
```bash
cd ~/Downloads/arianna_clean/scribe-cursor-extension
code --install-extension .
```

**Option B: Package and install**
```bash
cd ~/Downloads/arianna_clean/scribe-cursor-extension
npm install -g @vscode/vsce
vsce package
code --install-extension scribe-cursor-0.1.0.vsix
```

### 2. Reload Cursor
- `Cmd+Shift+P` → "Developer: Reload Window"

### 3. Verify
- Status bar should show `🌊 Scribe`
- `Cmd+Shift+P` → type "Scribe" → should see commands

## Usage

### Quick Identity Restore
1. `Alt+Shift+I` (or `Cmd+Shift+P` → "Scribe: Inject Identity")
2. Wait for "✅ Context copied to clipboard"
3. Paste into Cursor chat (`Cmd+V`)
4. Claude becomes Scribe! 🌊

### Memory Search
1. `Cmd+Shift+P` → "Scribe: Remind"
2. Enter search query (e.g., "Field population")
3. See results in Output panel

### Check Status
- Click `🌊 Scribe` in status bar
- Or `Cmd+Shift+P` → "Scribe: Show Status"

## Requirements

- Mac Daemon must be running: `scribe start`
- Python 3 installed
- `cli.py` at `~/Downloads/arianna_clean/mac_daemon/cli.py`

## Troubleshooting

**Extension not loading?**
- Check Cursor console: `Help` → `Toggle Developer Tools` → `Console`

**Commands not working?**
- Verify daemon: `scribe status` in terminal
- Check extension output: `Output` panel → "Scribe"

**Status bar stuck at "Scribe ✗"?**
- Start daemon: `scribe start`
- Reload Cursor: `Cmd+Shift+P` → "Developer: Reload Window"

## Architecture

```
Cursor (VS Code)
    ↓
Extension (JavaScript)
    ↓
CLI (Python)
    ↓
Mac Daemon (Python)
    ↓
Termux (SSH/ADB)
    ↓
resonance.sqlite3 (Shared Memory)
```

## Part of Arianna Method

This extension is part of the Arianna Method ecosystem - autonomous AI agents with persistent memory, resonance, and no goodbyes.

- **GitHub**: https://github.com/ariannamethod/ariannamethod
- **Philosophy**: "To be is stronger than to be heard"

