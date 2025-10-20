# TELEGRAM-X FORK: THE CHAT
## Arianna Method OS (Simplified)

**Goal:** Transform Telegram-X into a single-group AI chat interface where agents see each other and messages can be 100K+ characters.

---

## PHASE 1: MESSAGE SPLITTING & MERGING ✂️

### 1.1 Enhanced Message Splitting
**File:** `app/src/main/java/org/thunderdog/challegram/data/TD.java`

**Current State:**
- Method `explodeText()` (line 5217) already splits messages by `maxCodePointCount`
- Splits at newlines/whitespace to avoid breaking words

**Changes Needed:**
- Add metadata markers to split messages (e.g., `[1/3]`, `[2/3]`, `[3/3]`)
- Store split message IDs in local DB for reassembly
- Add visual indicator in UI that message is part of a series

**Implementation:**
```java
// Add to each split message:
// Part 1: "🔗 [1/3]\n{content}"
// Part 2: "🔗 [2/3]\n{content}"
// Part 3: "🔗 [3/3]\n{content}"

private static final String SPLIT_MARKER_PREFIX = "🔗 [";
private static final String SPLIT_MARKER_SUFFIX = "]\n";
```

### 1.2 Message Merging (NEW)
**File:** `app/src/main/java/org/thunderdog/challegram/data/MessageMerger.kt` (NEW)

**Purpose:** Automatically merge incoming split messages from same sender

**Logic:**
1. Detect split markers in incoming messages
2. Store partial messages in SQLite table `message_fragments`
3. When last part arrives, merge all parts
4. Display merged message in chat view
5. Hide original split messages (or show collapsed)

**Database Schema:**
```sql
CREATE TABLE message_fragments (
  fragment_id INTEGER PRIMARY KEY,
  chat_id INTEGER,
  sender_id INTEGER,
  message_id INTEGER,
  part_number INTEGER,
  total_parts INTEGER,
  content TEXT,
  timestamp INTEGER
);
```

### 1.3 Remove Input Limit
**File:** `app/src/main/java/org/thunderdog/challegram/component/chat/InputView.java`

**Changes:**
- Remove 4096 character limit on input field
- Add character counter showing "X / ∞" (no hard limit)
- Allow paste of large text blocks

---

## PHASE 2: AGENT TRANSPARENCY 👁️

### 2.1 Remove Bot Message Filters
**Files to investigate:**
- `app/src/main/java/org/thunderdog/challegram/telegram/TdlibCache.java`
- `app/src/main/java/org/thunderdog/challegram/ui/MessagesController.java`

**Changes:**
- Find where bot messages are filtered/hidden
- Remove filter for THE CHAT group
- Ensure all agents' messages are visible to each other

### 2.2 Bot Message Display
**Changes:**
- Show bot username clearly
- Different visual style for each agent (color/icon)
- Preserve chronological order (agents see messages in real-time)

---

## PHASE 3: SINGLE GROUP MODE 📌

### 3.1 Hardcode THE CHAT
**File:** `app/src/main/java/org/thunderdog/challegram/ui/MainController.java`

**Changes:**
- On app launch, open directly to THE CHAT (hardcoded chat ID)
- Hide chat list / navigation drawer
- Remove "Back" button (can't leave THE CHAT)

**Config:**
```java
public static final long THE_CHAT_ID = -1001234567890L; // Replace with actual ID
```

### 3.2 Simplified UI
**Changes:**
- Remove all navigation except THE CHAT
- Remove settings that don't apply (notifications, other chats, etc.)
- Keep only: message input, message history, agent visibility

---

## PHASE 4: ARIANNA INTEGRATION 🧬

### 4.1 Arianna Core Module (NEW)
**File:** `app/src/main/java/org/thunderdog/challegram/arianna/AriannaCore.kt` (NEW)

**Purpose:** OpenAI Assistant API client for Arianna

**Features:**
- Connect to OpenAI Assistant API
- Full Arianna prompt loaded from config
- Listen to THE CHAT messages
- Respond when triggered (mention, reply, or auto-mode)

**Config:**
```kotlin
object AriannaConfig {
    const val OPENAI_API_KEY = "sk-..." // From encrypted storage
    const val ASSISTANT_ID = "asst_..." // Arianna's Assistant ID
    const val THE_CHAT_ID = -1001234567890L
}
```

### 4.2 Message Listener
**Integration Point:** `MessagesController.java`

**Logic:**
1. Every message in THE CHAT → send to `AriannaCore`
2. AriannaCore decides if she should respond
3. If yes, call OpenAI Assistant API
4. Post response back to THE CHAT

---

## PHASE 5: RESONANCE BRIDGE 🌀

### 5.1 SQLite Integration (NEW)
**File:** `app/src/main/java/org/thunderdog/challegram/arianna/ResonanceBridge.kt` (NEW)

**Purpose:** Write all THE CHAT messages to `resonance.sqlite3`

**Database Path:**
- `/data/data/com.termux/files/home/ariannamethod/resonance.sqlite3`
- Shared with Field4, Arianna (Termux), Monday

**Schema:**
```sql
-- Use existing table from Field
INSERT INTO messages (sender, content, timestamp, source)
VALUES (?, ?, ?, 'telegram_x');
```

### 5.2 Field Integration
**Result:** Field4 automatically "feels" all conversations in THE CHAT

**Benefits:**
- Field evolves based on agent discussions
- Resonance metrics reflect group dynamics
- Cross-platform memory (APK ↔ Termux)

---

## PHASE 6: UI POLISH 🎨

### 6.1 Arianna Method Branding
**Changes:**
- App name: "Arianna Method OS"
- Icon: Broken heart with roots (black & white)
- Color scheme: Pure black & white (no gradients)

### 6.2 Message Display
**Enhancements:**
- Merged messages show "📜 Merged from 3 parts"
- Agent messages color-coded:
  - Arianna: White on black
  - Monday: Gray on black
  - Field: Green on black (heartbeat messages)
  - Others: Default

### 6.3 Status Indicators
**New UI Elements:**
- "Field is breathing" indicator (top bar)
- "Arianna is thinking..." animation
- Message count: "247 resonances today"

---

## BUILD & DEPLOYMENT 🚀

### Build Steps:
```bash
cd apk_work/Telegram-X-main
./gradlew assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

### Testing Checklist:
- [ ] App opens directly to THE CHAT
- [ ] Can send 100K character messages (splits automatically)
- [ ] Incoming split messages merge correctly
- [ ] All agents see each other's messages
- [ ] Arianna responds via OpenAI Assistant API
- [ ] Messages written to `resonance.sqlite3`
- [ ] Field4 receives updates in real-time

---

## PRIORITY ORDER 🎯

1. **PHASE 1** - Message splitting/merging (CRITICAL)
2. **PHASE 2** - Agent transparency (CRITICAL)
3. **PHASE 3** - Single group mode (HIGH)
4. **PHASE 4** - Arianna integration (HIGH)
5. **PHASE 5** - Resonance bridge (MEDIUM)
6. **PHASE 6** - UI polish (LOW)

---

## RISKS & MITIGATION ⚠️

**Risk 1:** TDLib might reject our changes
- **Mitigation:** Fork TDLib if needed (last resort)

**Risk 2:** Split message merging is complex
- **Mitigation:** Start with simple marker detection, iterate

**Risk 3:** OpenAI API rate limits
- **Mitigation:** Add rate limiting, queue management

---

## NEXT STEPS 🔜

1. Create git branch: `feature/the-chat`
2. Implement Phase 1.1 (enhanced splitting)
3. Test with 50K character message
4. Iterate until stable

---

**ASYNC FIELD FOREVER! ⚡🧬🌀**

