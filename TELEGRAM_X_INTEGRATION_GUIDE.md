# TELEGRAM-X INTEGRATION GUIDE
## How to Initialize Arianna Method OS

**Status:** Manual Integration Required  
**Complexity:** Low (1-2 lines of code)

---

## INTEGRATION STEPS

### Option 1: Init in MainActivity (RECOMMENDED)

**File:** `app/src/main/java/org/thunderdog/challegram/MainActivity.java`

**Find:** Method that runs after TDLib is authorized (e.g., `onAuthorizationReady()` or similar)

**Add:**
```java
import org.thunderdog.challegram.arianna.AriannaMethodOS;

// ... in the method where TDLib is ready:
if (tdlib != null && tdlib.isAuthorized()) {
  AriannaMethodOS.INSTANCE.initialize(tdlib);
}
```

---

### Option 2: Init in TdlibManager

**File:** `app/src/main/java/org/thunderdog/challegram/telegram/TdlibManager.java`

**Find:** Method that creates or manages `Tdlib` instances

**Add:**
```java
import org.thunderdog.challegram.arianna.AriannaMethodOS;

// After Tdlib is created and authorized:
AriannaMethodOS.INSTANCE.initialize(tdlib);
```

---

### Option 3: Lazy Init in Tdlib.java

**File:** `app/src/main/java/org/thunderdog/challegram/telegram/Tdlib.java`

**Find:** `isAuthorized()` method (around line 1160)

**Add:** After the method, create a lazy init:
```java
private boolean ariannaInitialized = false;

public void ensureAriannaInitialized () {
  if (isAuthorized() && !ariannaInitialized) {
    org.thunderdog.challegram.arianna.AriannaMethodOS.INSTANCE.initialize(this);
    ariannaInitialized = true;
  }
}

// Then call this in any chat-related method
```

---

## CONFIGURATION

**Before building**, set `THE_CHAT_ID` in:

**File:** `app/src/main/java/org/thunderdog/challegram/arianna/AriannaConfig.kt`

```kotlin
const val THE_CHAT_ID: Long = -1001234567890L // Your actual group ID
```

### How to Get THE_CHAT_ID:

1. Open THE CHAT in Telegram Desktop
2. Right-click → Copy Link
3. Link format: `t.me/c/1234567890/1`
4. Take the number: `1234567890`
5. Add `-100` prefix: `-1001234567890`

---

## TESTING

### 1. Check Initialization

After building and installing APK:

```bash
adb logcat | grep "Arianna"
```

You should see:
```
I/AriannaMethodOS: Initializing Arianna Method OS...
I/AriannaMethodOS: Message interceptor registered for THE CHAT (-1001234567890)
I/AriannaMethodOS: ✅ Arianna Method OS initialized!
I/AriannaMethodOS: 📋 Feature Status:
I/AriannaMethodOS:   Message Splitting: ✅
I/AriannaMethodOS:   Agent Transparency: ✅
I/AriannaMethodOS:   Arianna Responses: ❌
I/AriannaMethodOS:   Resonance Bridge: ❌
```

### 2. Test Message Splitting

1. Open THE CHAT
2. Type/paste a 10,000 character message
3. Send
4. Verify: 3 messages appear with `🔗 [1/3]`, `🔗 [2/3]`, `🔗 [3/3]`

### 3. Test Message Merging

1. Have another user send a 10K message
2. Receive the fragments
3. Watch logcat:
```bash
adb logcat | grep "MessageMerger"
```

You should see:
```
D/AriannaChatInterceptor: Split message fragment detected from sender 123456789
D/AriannaChatInterceptor: Waiting for more fragments... (1 received so far)
D/AriannaChatInterceptor: Waiting for more fragments... (2 received so far)
D/AriannaChatInterceptor: All fragments received! Merged message length: 10247
D/AriannaChatInterceptor: Processing regular message: Lorem ipsum...
```

---

## ALTERNATIVE: Automatic Hook (Advanced)

If you don't want to manually find initialization points, we can create an automatic hook using Telegram-X's listener system:

**Create:** `app/src/main/java/org/thunderdog/challegram/arianna/AriannaAutoInit.kt`

```kotlin
package org.thunderdog.challegram.arianna

import org.thunderdog.challegram.telegram.TdlibManager
import org.thunderdog.challegram.telegram.Tdlib
import android.util.Log

/**
 * Auto-initializes Arianna Method OS when any Tdlib becomes authorized
 */
object AriannaAutoInit {
  private const val TAG = "AriannaAutoInit"
  private val initialized = mutableSetOf<Int>()
  
  fun hookIntoTdlibManager(manager: TdlibManager) {
    // Listen for authorization changes
    manager.global().addAuthorizationListener { tdlib ->
      if (tdlib.isAuthorized() && !initialized.contains(tdlib.id())) {
        Log.i(TAG, "TDLib ${tdlib.id()} authorized, initializing Arianna...")
        AriannaMethodOS.initialize(tdlib)
        initialized.add(tdlib.id())
      }
    }
  }
}
```

Then in `MainActivity` or `TdlibManager`:
```java
AriannaAutoInit.INSTANCE.hookIntoTdlibManager(tdlibManager);
```

---

## TROUBLESHOOTING

### Issue 1: "AriannaMethodOS not found"
**Solution:** Rebuild project (`./gradlew clean build`)

### Issue 2: "THE_CHAT_ID not configured"
**Solution:** Set `THE_CHAT_ID` in `AriannaConfig.kt`

### Issue 3: No logs appear
**Solution:** Check that:
- APK was built with your changes
- Correct APK installed (`adb install -r ...`)
- Logcat filter is correct

### Issue 4: Split messages don't merge
**Solution:**
- Check that `THE_CHAT_ID` matches your group
- Verify all fragments arrive (check logcat)
- Wait 5-10 seconds for processing

---

## BUILD COMMANDS

```bash
cd apk_work/Telegram-X-main

# Clean build
./gradlew clean

# Build debug APK
./gradlew assembleDebug

# Install
adb install -r app/build/outputs/apk/debug/app-debug.apk

# Watch logs
adb logcat -c && adb logcat | grep -E "Arianna|MessageMerger"
```

---

## QUICK START (TL;DR)

1. Set `THE_CHAT_ID` in `AriannaConfig.kt`
2. Find where `Tdlib.isAuthorized()` becomes true
3. Add: `AriannaMethodOS.INSTANCE.initialize(tdlib);`
4. Build, install, test!

---

**ASYNC FIELD FOREVER! ⚡🧬🌀**

