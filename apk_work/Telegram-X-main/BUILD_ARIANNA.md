# BUILD ARIANNA METHOD OS

**Quick guide to build Telegram-X with Arianna Method features**

---

## PREREQUISITES

- **macOS** or **Linux**
- **Android SDK 35**
- **JDK 17**
- **Git** with LFS (`brew install git git-lfs`)

---

## STEP 1: CONFIGURE

### Set THE_CHAT_ID

**File:** `app/src/main/java/org/thunderdog/challegram/arianna/AriannaConfig.kt`

```kotlin
const val THE_CHAT_ID: Long = -1001234567890L // ← Replace with your group ID
```

**How to get group ID:**
1. Open group in Telegram Desktop
2. Right-click → Copy Link
3. Link: `t.me/c/1234567890/1`
4. Add `-100` prefix: `-1001234567890`

---

## STEP 2: INTEGRATE (One-time)

**Choose ONE method:**

### Method A: Quick Hook (Recommended)

Add to `app/src/main/java/org/thunderdog/challegram/MainActivity.java`:

```java
import org.thunderdog.challegram.arianna.AriannaMethodOS;

// In onCreate() or onResume(), after TDLib is ready:
private void initializeAriannaOS() {
  Tdlib tdlib = TDLib.instance().currentTdlib();
  if (tdlib != null && tdlib.isAuthorized()) {
    AriannaMethodOS.INSTANCE.initialize(tdlib);
  }
}
```

### Method B: Auto-detect (Advanced)

See `TELEGRAM_X_INTEGRATION_GUIDE.md` for listener-based approach.

---

## STEP 3: BUILD

```bash
cd apk_work/Telegram-X-main

# Setup (first time only)
./scripts/setup.sh

# Clean build
./gradlew clean

# Build debug APK
./gradlew assembleDebug
```

**Output:** `app/build/outputs/apk/debug/app-debug.apk`

---

## STEP 4: INSTALL

```bash
# Install to device
adb install -r app/build/outputs/apk/debug/app-debug.apk

# Verify installation
adb shell pm list packages | grep challegram
```

---

## STEP 5: TEST

### Test 1: Check Logs

```bash
adb logcat -c  # Clear logs
adb logcat | grep -E "Arianna|MessageMerger"
```

Expected output:
```
I/AriannaMethodOS: ✅ Arianna Method OS initialized!
I/AriannaMethodOS:   Message Splitting: ✅
```

### Test 2: Send Long Message

1. Open THE CHAT
2. Paste 10,000 character text
3. Send
4. Verify: 3 messages with `🔗 [1/3]`, `🔗 [2/3]`, `🔗 [3/3]`

### Test 3: Receive Long Message

1. Another user sends 10K message
2. Watch logcat for "All fragments received!"
3. Verify merged message appears

---

## TROUBLESHOOTING

### Build Fails

```bash
# Check Java version
java -version  # Should be 17

# Check Android SDK
echo $ANDROID_HOME

# Clean and retry
./gradlew clean build
```

### Installation Fails

```bash
# Uninstall old version
adb uninstall org.thunderdog.challegram

# Reinstall
adb install app/build/outputs/apk/debug/app-debug.apk
```

### No Logs Appear

```bash
# Check device is connected
adb devices

# Ensure correct package
adb logcat | grep "org.thunderdog.challegram"

# Full log dump
adb logcat > logcat.txt
```

---

## BUILD VARIANTS

### Debug Build (Default)
- Package: `org.thunderdog.challegram.debug`
- Debuggable, verbose logs
- For development/testing

```bash
./gradlew assembleDebug
```

### Release Build
- Package: `org.thunderdog.challegram`
- Optimized, signed
- For distribution

```bash
./gradlew assembleRelease
```

---

## NEXT STEPS

After successful build:

1. **Phase 2:** Remove bot filters (agent transparency)
2. **Phase 3:** Hardcode THE_CHAT (single group mode)
3. **Phase 4:** Add Arianna API integration
4. **Phase 5:** Connect to resonance.sqlite3
5. **Phase 6:** UI polish & branding

See `TELEGRAM_X_FORK_PLAN.md` for details.

---

## NEED HELP?

- **Integration issues:** See `TELEGRAM_X_INTEGRATION_GUIDE.md`
- **Code documentation:** See `app/src/main/java/org/thunderdog/challegram/arianna/README.md`
- **Phase status:** See `TELEGRAM_X_STATUS.md`

---

**ASYNC FIELD FOREVER! ⚡🧬🌀**

