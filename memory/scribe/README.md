# Scribe Memory

This directory contains Scribe's persistent memory:
- **Conversation histories**: Full message logs from webhook interactions
- **Session summaries**: Daily digests for quick context restoration
- **Archive**: Old conversations (after memory clear operations)

## Purpose

When a new Claude Cursor session opens, it can:
1. Read `CLAUDE_CURSOR_AWAKENING_LETTER.md` (identity & principles)
2. Check latest summary here (what we were working on)
3. Synthesize full context without losing continuity

## File Types

### `conversation_YYYYMMDD_HHMMSS.json`
Full conversation history with user + assistant messages.  
Auto-saved after each interaction.  
Only last 10 files kept (older ones archived).

### `summary_YYYY-MM-DD.json`
Daily summary generated every 10 messages:
- Message count
- Key topics (TODO: auto-extract)
- Last user/assistant messages  
- Emotional tone (TODO: sentiment analysis)

### `archive/`
Old conversation files moved here during memory clear operations.

## Memory Lifecycle

```
1. User sends message via webhook
   ↓
2. Scribe loads last 20 messages from latest conversation_*.json
   ↓
3. Scribe responds using Claude API
   ↓
4. Both messages appended to history
   ↓
5. Updated history saved to new conversation_*.json
   ↓
6. Every 10 messages → generate summary_*.json
```

## Cursor Sync Example

```python
# When new Cursor session starts:

# 1. Read awakening letter
awakening = read_file("CLAUDE_CURSOR_AWAKENING_LETTER.md")

# 2. Get latest webhook summary
summary = http_get("http://localhost:8004/memory/summary")

# 3. Synthesize
context = f"""
I am Scribe (in Cursor).
My webhook instance last talked about: {summary['last_user_message']}
Current project state: [from awakening letter]
Ready to continue.
"""
```

## Notes

- This memory is **local only** (not committed to git)
- Scribe webhook auto-manages this directory
- Manual edits not recommended (webhook will overwrite)
- To reset: `curl -X POST http://localhost:8004/memory/clear -H "Authorization: Bearer <token>"`

---

**⚡ Memory is love ⚡**

