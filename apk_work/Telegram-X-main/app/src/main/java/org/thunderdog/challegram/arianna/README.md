# Arianna Method OS - Package

**Location:** `app/src/main/java/org/thunderdog/challegram/arianna/`

This package contains all Arianna Method-specific features integrated into Telegram-X.

---

## Files

### 1. `AriannaMethodOS.kt` 🚀
**Main entry point** for Arianna Method initialization.

**Usage:**
```kotlin
// In MainActivity or TdlibManager after TDLib is ready:
AriannaMethodOS.initialize(tdlib)

// On app shutdown:
AriannaMethodOS.shutdown(tdlib)
```

**Features:**
- Registers message interceptor
- Starts cleanup timer
- Logs feature status

---

### 2. `AriannaConfig.kt` ⚙️
**Configuration constants** for all Arianna Method features.

**Key Settings:**
```kotlin
const val THE_CHAT_ID: Long = -1001234567890L // Set your group ID
const val ENABLE_MESSAGE_SPLITTING = true
const val ENABLE_AGENT_TRANSPARENCY = true
```

**TODO Before Release:**
- Set actual `THE_CHAT_ID`
- Configure OpenAI API keys (Phase 4)
- Set resonance DB path (Phase 5)

---

### 3. `MessageMerger.kt` ✂️
**Merges split messages** marked with `🔗 [X/Y]`.

**API:**
```kotlin
// Check if message is split
MessageMerger.isSplitMessage(text: String): Boolean

// Add fragment and get merged result
MessageMerger.addFragment(
  chatId, senderId, messageId, timestamp, formattedText
): TdApi.FormattedText?

// Parse marker: 🔗 [2/5] → Pair(2, 5)
MessageMerger.parseSplitMarker(text: String): Pair<Int, Int>?

// Cleanup old fragments
MessageMerger.cleanupOldFragments(currentTimestamp: Long)
```

**Storage:**
- In-memory cache (by chat → sender → part number)
- Auto-cleanup after 5 minutes

---

### 4. `AriannaChatInterceptor.kt` 📡
**Intercepts messages** in THE CHAT for processing.

**Responsibilities:**
1. Detect split message fragments
2. Call `MessageMerger` to reassemble
3. Write to resonance.sqlite3 (Phase 5)
4. Trigger Arianna responses (Phase 4)

**Message Flow:**
```
TDLib → MessageListener → AriannaChatInterceptor
  ↓
  Split message? 
    Yes → MessageMerger → Merge → Process
    No  → Process directly
```

---

## Integration Points

### How Split Messages Work

**Sending (TD.java):**
```java
// In TD.explodeText():
1. Split message into 4K chunks
2. Add markers: 🔗 [1/3], 🔗 [2/3], 🔗 [3/3]
3. Send each part separately
```

**Receiving (AriannaChatInterceptor):**
```kotlin
1. Detect marker in incoming message
2. Store fragment in MessageMerger
3. When all parts received → merge
4. Display merged message
5. Hide individual fragments
```

---

## Phase Status

### ✅ Phase 1: Message Splitting/Merging
- [x] Enhanced `explodeText()` with markers
- [x] `MessageMerger` module
- [x] `AriannaChatInterceptor` integration
- [ ] UI: Hide fragments, show merged (TODO)

### 🔜 Phase 2: Agent Transparency
- [ ] Remove bot message filters
- [ ] Test with multiple bots

### 🔜 Phase 3: Single Group Mode
- [ ] Hardcode THE_CHAT_ID
- [ ] Hide navigation
- [ ] Simplified UI

### 🔜 Phase 4: Arianna Integration
- [ ] `AriannaCore.kt` - OpenAI API client
- [ ] Auto-response logic
- [ ] Rate limiting

### 🔜 Phase 5: Resonance Bridge
- [ ] `ResonanceBridge.kt` - SQLite writer
- [ ] Schema: messages table
- [ ] Field4 receives updates

### 🔜 Phase 6: UI Polish
- [ ] Branding (icon, colors)
- [ ] Merged message indicator
- [ ] Field status badge

---

## Testing

### Test 1: Split Message Send
```
1. Open THE CHAT
2. Paste 10,000 character text
3. Send
4. Verify: 3 messages with 🔗 [1/3], 🔗 [2/3], 🔗 [3/3]
```

### Test 2: Split Message Receive
```
1. Another user sends 10K character message
2. Receive 3 fragments
3. Verify: Auto-merged into single message
4. Verify: Fragments hidden in UI
```

### Test 3: Fragment Cleanup
```
1. Send incomplete split message (1/3, 2/3 only)
2. Wait 5+ minutes
3. Verify: Fragments removed from memory
```

---

## Known Issues

### Issue 1: UI Not Hiding Fragments
**Status:** TODO  
**Fix:** Modify chat adapter to detect merged messages and hide originals

### Issue 2: Entities (formatting) Lost on Merge
**Status:** Known limitation  
**Fix:** Implement proper entity merging in `MessageMerger.mergeFragments()`

### Issue 3: THE_CHAT_ID Not Set
**Status:** Configuration needed  
**Fix:** User must set actual group ID in `AriannaConfig.kt`

---

## Future Enhancements

1. **Persistent Fragment Storage**
   - Currently in-memory only
   - Add SQLite cache for app restarts

2. **Smart Merging**
   - Detect related messages without markers
   - Use AI to merge conversational threads

3. **Progress Indicator**
   - Show "Receiving 2/5 parts..." in UI
   - Real-time merge progress

4. **Cross-Device Sync**
   - Share merge state via Telegram cloud
   - Seamless experience across devices

---

## Contributing

When modifying this package:
1. Keep changes minimal and focused
2. Log all operations (use `Log.d()`)
3. Update this README
4. Test on physical device (not emulator)

---

**ASYNC FIELD FOREVER! ⚡🧬🌀**

