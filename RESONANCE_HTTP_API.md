# Resonance HTTP API Documentation

**Status:** ✅ LIVE
**Endpoint:** `http://localhost:8080`
**Server:** Python HTTP Server on Termux
**Purpose:** Cross-app access to `resonance.sqlite3`

---

## Quick Start

### Start Server
```bash
~/ariannamethod/termux/start_resonance_server.sh
```

### Stop Server
```bash
# Find PID
cat ~/ariannamethod/logs/resonance_api.pid

# Kill server
kill $(cat ~/ariannamethod/logs/resonance_api.pid)
rm ~/ariannamethod/logs/resonance_api.pid
```

### Check Logs
```bash
tail -f ~/ariannamethod/logs/resonance_api.log
```

---

## API Endpoints

### 1. Health Check

**GET** `/health`

Returns server status and database info.

**Example:**
```bash
curl http://localhost:8080/health
```

**Response:**
```json
{
  "status": "ok",
  "db_path": "/data/data/com.termux/files/home/ariannamethod/resonance.sqlite3",
  "db_size_bytes": 2543235072,
  "db_size_mb": 2425.42,
  "note_count": 16516,
  "timestamp": "2025-11-11T04:23:38.346148"
}
```

---

### 2. Get Recent Notes

**GET** `/resonance/recent?limit=N`

Returns N most recent notes from resonance bus.

**Parameters:**
- `limit` (optional): Number of notes to return (default: 100)

**Example:**
```bash
curl "http://localhost:8080/resonance/recent?limit=10"
```

**Response:**
```json
{
  "status": "ok",
  "count": 10,
  "limit": 10,
  "notes": [
    {
      "timestamp": "2025-11-11T04:22:49.621973",
      "content": "👁️ Monitoring .claude-defender/...",
      "context": "infrastructure_monitoring",
      "source": "defender_daemon"
    },
    ...
  ]
}
```

**Use Cases:**
- Molly Widget: Read recent resonance events for monologue integration
- Arianna Method APK: Display recent system activity
- Mac daemon: Monitor Termux activity

---

### 3. Get Notes Since Timestamp

**GET** `/resonance/since?timestamp=YYYY-MM-DD HH:MM:SS`

Returns all notes created after specified timestamp.

**Parameters:**
- `timestamp` (required): ISO format timestamp or SQL datetime string

**Examples:**
```bash
# ISO format
curl "http://localhost:8080/resonance/since?timestamp=2025-11-11T04:20:00"

# SQL format (URL-encoded)
curl "http://localhost:8080/resonance/since?timestamp=2025-11-11%2004:20:00"
```

**Response:**
```json
{
  "status": "ok",
  "since": "2025-11-11 04:20:00",
  "count": 783,
  "notes": [ ... ]
}
```

**Use Cases:**
- Incremental sync for Mac daemon
- Delta updates for Molly Widget
- Real-time event streaming

---

### 4. Write New Note

**POST** `/resonance/write`

Writes a new note to resonance.sqlite3.

**Headers:**
- `Content-Type: application/json`

**Body:**
```json
{
  "content": "Note content here",
  "source": "source_identifier",
  "context": "optional_context",
  "timestamp": "optional_timestamp"
}
```

**Required Fields:**
- `content`: The note content (string)
- `source`: Source identifier (string)

**Optional Fields:**
- `context`: Additional context (string, default: "")
- `timestamp`: Custom timestamp (string, default: current time)

**Example:**
```bash
curl -X POST http://localhost:8080/resonance/write \
  -H "Content-Type: application/json" \
  -d '{
    "content": "User action: tapped widget",
    "source": "molly_widget",
    "context": "user_interaction"
  }'
```

**Response:**
```json
{
  "status": "ok",
  "message": "Note written successfully",
  "timestamp": "2025-11-11T04:24:08.519863",
  "source": "molly_widget"
}
```

**Use Cases:**
- Molly Widget: Log user interactions
- Arianna Method APK: Write voice transcriptions
- Mac daemon: Write remote observations

---

## Integration Examples

### Molly Widget (Kotlin)

```kotlin
// Read recent resonance events
val url = URL("http://localhost:8080/resonance/recent?limit=50")
val connection = url.openConnection() as HttpURLConnection
connection.requestMethod = "GET"

val response = connection.inputStream.bufferedReader().readText()
val json = JSONObject(response)
val notes = json.getJSONArray("notes")

// Write event
val writeUrl = URL("http://localhost:8080/resonance/write")
val writeConnection = writeUrl.openConnection() as HttpURLConnection
writeConnection.requestMethod = "POST"
writeConnection.setRequestProperty("Content-Type", "application/json")
writeConnection.doOutput = true

val payload = JSONObject()
payload.put("content", "Widget action")
payload.put("source", "molly_widget")
payload.put("context", "user_tap")

writeConnection.outputStream.write(payload.toString().toByteArray())
```

### Mac Daemon (Python)

```python
import requests
from datetime import datetime

# Read recent notes
response = requests.get("http://localhost:8080/resonance/recent?limit=100")
data = response.json()
notes = data["notes"]

# Incremental sync
last_sync = "2025-11-11 04:00:00"
response = requests.get(
    "http://localhost:8080/resonance/since",
    params={"timestamp": last_sync}
)
new_notes = response.json()["notes"]

# Write observation
requests.post(
    "http://localhost:8080/resonance/write",
    json={
        "content": "Mac daemon observation",
        "source": "mac_daemon",
        "context": "remote_monitoring"
    }
)
```

### Linux Defender (Bash/curl)

```bash
# Monitor new events every 5 seconds
LAST_CHECK=$(date -Iseconds)
while true; do
  sleep 5
  NEW_NOTES=$(curl -s "http://localhost:8080/resonance/since?timestamp=$LAST_CHECK")
  COUNT=$(echo "$NEW_NOTES" | jq -r '.count')

  if [ "$COUNT" -gt 0 ]; then
    echo "Found $COUNT new notes"
    # Process notes...
  fi

  LAST_CHECK=$(date -Iseconds)
done
```

---

## Server Management

### Auto-Start on Boot

Add to `~/ariannamethod/boot_scripts/arianna_system_init.sh`:

```bash
# Resonance HTTP API Server
start_component "Resonance HTTP API" \
    "nohup python3 $HOME/ariannamethod/termux/resonance_http_server.py" \
    "resonance_http_api"
```

### Check if Running

```bash
if [ -f ~/ariannamethod/logs/resonance_api.pid ]; then
  PID=$(cat ~/ariannamethod/logs/resonance_api.pid)
  if kill -0 "$PID" 2>/dev/null; then
    echo "✅ Server running (PID: $PID)"
  else
    echo "❌ Server not running"
  fi
fi
```

---

## Architecture

```
┌─────────────────┐
│  Molly Widget   │
│   (Android)     │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────────────┐
│  Resonance HTTP Server  │
│  (Termux localhost:8080)│
└────────┬────────────────┘
         │ SQLite
         ▼
┌──────────────────────┐
│  resonance.sqlite3   │
│    (2.4GB, 16K+)     │
└──────────────────────┘
         ▲
         │ Direct access
         │
┌────────┴────────┐
│ Termux Daemons  │
│ (Defender, etc) │
└─────────────────┘
```

**Benefits:**
- ✅ Cross-app communication (no scoped storage issues)
- ✅ Remote access (Mac/Linux can query)
- ✅ Real-time sync (HTTP polling)
- ✅ Simple protocol (standard HTTP/JSON)
- ✅ No special permissions needed

---

## Troubleshooting

### Server won't start
```bash
# Check if port is in use
netstat -an | grep 8080

# Check logs
tail -50 ~/ariannamethod/logs/resonance_api.log

# Try manual start
python3 ~/ariannamethod/termux/resonance_http_server.py
```

### Connection refused
```bash
# Verify server is running
ps aux | grep resonance_http_server

# Test locally
curl http://localhost:8080/health

# Check firewall (if accessing remotely)
```

### Database locked
```bash
# Check for long-running transactions
sqlite3 ~/ariannamethod/resonance.sqlite3 "PRAGMA wal_checkpoint(TRUNCATE);"
```

---

**Server Implementation:** `~/ariannamethod/termux/resonance_http_server.py`
**Start Script:** `~/ariannamethod/termux/start_resonance_server.sh`
**Logs:** `~/ariannamethod/logs/resonance_api.log`
**PID File:** `~/ariannamethod/logs/resonance_api.pid`

🛡️ Implemented by Claude Defender
🔵 Requested by Scribe
🟢 Approved by User
