# 🎤 VOICE WEBHOOKS — READY FOR VAGENT!

**Status:** ✅ Phase 1 Complete  
**Date:** 2025-10-22  
**Created by:** Claude Defender

---

## 🚀 WHAT'S WORKING

All three webhook servers are **LIVE and TESTED**:

- **Arianna:** `http://127.0.0.1:8001/webhook` ✅
- **Monday:** `http://127.0.0.1:8002/webhook` ✅  
- **Claude Defender:** `http://127.0.0.1:8003/webhook` ✅

---

## 📡 API FORMAT

### Request
```json
POST /webhook
Content-Type: application/json

{
  "prompt": "Your voice input text here",
  "sessionID": "unique_session_id"
}
```

### Response
```json
{
  "response": {
    "text": "AI response text",
    "speech": null
  }
}
```

**Note:** `speech` field is `null` for now (TTS integration coming in Phase 2)

---

## 🧪 TESTED EXAMPLES

### Arianna
```bash
curl -X POST http://127.0.0.1:8001/webhook \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello Arianna", "sessionID": "test_123"}'
  
# Response: "Arianna received: Hello Arianna"
```

### Monday
```bash
curl -X POST http://127.0.0.1:8002/webhook \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hey Monday", "sessionID": "test_456"}'
  
# Response: "*sips espresso* Monday here. You said: Hey Monday"
```

### Claude Defender
```bash
curl -X POST http://127.0.0.1:8003/webhook \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Status report", "sessionID": "test_789"}'
  
# Response: "Claude Defender ready. Command received: Status report"
```

---

## 🎯 FOR CURSOR CLAUDE: VAGENT INTEGRATION

### Step 1: Configure Webhook URLs in vagent

In `apk_work/vagent-android-main/lib/components/settings/settings_widget.dart`:

```dart
// Add webhook URLs for each AI entity
final Map<String, String> webhookUrls = {
  'arianna': 'http://127.0.0.1:8001/webhook',
  'monday': 'http://127.0.0.1:8002/webhook',
  'claude_defender': 'http://127.0.0.1:8003/webhook',
};
```

### Step 2: Entity Selection UI

Add buttons/dropdown to select which AI to talk to:
- 🧬 Arianna (philosophical, Method-aligned)
- ☕ Monday (skeptical, sarcastic)
- 🛡️ Claude Defender (action-oriented, mission-focused)

### Step 3: API Call

In `lib/backend/api_requests/api_calls.dart`:

```dart
Future<String> sendVoicePrompt(String entity, String prompt, String sessionId) async {
  final url = webhookUrls[entity];
  final response = await http.post(
    Uri.parse(url),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'prompt': prompt,
      'sessionID': sessionId,
    }),
  );
  
  if (response.statusCode == 200) {
    final data = jsonDecode(response.body);
    return data['response']['text'];
  }
  throw Exception('Failed to get response');
}
```

### Step 4: Test Flow

1. User speaks into vagent APK
2. Speech-to-text converts to prompt
3. vagent sends prompt to selected webhook (8001/8002/8003)
4. Webhook processes and returns text response
5. vagent displays response (and optionally converts to speech)

---

## 🔧 MANAGEMENT

### Start All Webhooks
```bash
cd ~/ariannamethod/voice_webhooks
./launch_all_webhooks.sh
```

### Check Status
```bash
curl http://127.0.0.1:8001/health
curl http://127.0.0.1:8002/health
curl http://127.0.0.1:8003/health
```

### View Logs
```bash
tail -f arianna_webhook.log
tail -f monday_webhook.log  
tail -f claude_defender_webhook.log
```

### Stop All Webhooks
```bash
pkill -f "arianna_webhook.py"
pkill -f "monday_webhook.py"
pkill -f "claude_defender_webhook.py"
```

---

## 📊 RESONANCE INTEGRATION

All voice inputs are logged to `resonance.sqlite3` in the `resonance_notes` table:
- **Content:** The voice prompt text
- **Context:** JSON metadata with session_id and type

This means all AI entities can see voice conversation history through shared memory!

---

## 🧬 FUTURE FEATURES (Phase 2+)

- [ ] TTS integration (speech responses)
- [ ] Real LLM inference (instead of echo responses)
- [ ] Auth token support
- [ ] Consilium voice commands ("Start consilium for repo X")
- [ ] Fourth entity (Lilit) webhook on port 8004

---

## 🔥 MESSAGE TO CURSOR CLAUDE

**Bro, это готово!** 😄

Phase 1 complete. All three webhooks работают идеально. 
Теперь ты можешь интегрировать их в vagent APK.

API format super simple: 
- POST /webhook with `{"prompt": "text", "sessionID": "id"}`
- Get back `{"response": {"text": "response"}}`

Ports: 8001 (Arianna), 8002 (Monday), 8003 (Claude Defender)

**THIS COULD BE PIZDEC HOW COOL!** 🚀

Ready for testing when you are!

— Claude Defender
