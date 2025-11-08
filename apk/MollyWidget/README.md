# Molly - Android Home Screen Widget

Minimal Android widget showing Molly Bloom's evolving monologue from Joyce's Ulysses.

## What it does

- **Displays 5-6 lines** of Molly's monologue on your home screen
- **Updates automatically** every 3 minutes
- **Weaves your phrases** into the monologue stream (doesn't reply - integrates)
- **Uses metrics** (entropy, perplexity, resonance) to find insertion points
- **Can break words** when inserting phrases (like the original: "migh [PHRASE] t")
- **Connects to resonance.sqlite3** if ariannamethod ecosystem is present
- **Cannot be reset** - monologue mutates permanently (only reinstall resets)

## Build Instructions

### Prerequisites

- Android Studio or Android SDK command-line tools
- JDK 17+
- Android SDK API 34

### Building APK

#### Option 1: Android Studio (Recommended)

1. Open Android Studio
2. **File → Open** → Select the `android/` directory
3. Wait for Gradle sync to complete
4. **Build → Build Bundle(s) / APK(s) → Build APK(s)**
5. APK will be in: `android/app/build/outputs/apk/debug/app-debug.apk`

#### Option 2: Command Line (with Gradle wrapper)

```bash
cd /workspace/android

# First time setup - create Gradle wrapper
gradle wrapper

# Build APK
./gradlew assembleDebug

# APK location
ls -lh app/build/outputs/apk/debug/app-debug.apk
```

#### Option 3: Command Line (with system Gradle)

```bash
cd /workspace/android

# Build
gradle assembleDebug

# Find APK
find . -name "*.apk"
```

### Installing APK

```bash
# Install to connected device
adb install app/build/outputs/apk/debug/app-debug.apk

# Or manually copy APK to phone and install
```

## Usage

1. **Add widget**: Long-press home screen → Widgets → Molly
2. **Read monologue**: Widget updates every 3 minutes
3. **Input text**: Tap widget → Enter text (max 100 chars) → Press Enter
4. **Watch integration**: Your phrase appears woven into the monologue

## Architecture

```
android/
├── app/
│   ├── src/main/
│   │   ├── assets/
│   │   │   └── molly.md              # Original Ulysses text
│   │   ├── java/com/ariannamethod/molly/
│   │   │   ├── MollyWidget.kt        # AppWidgetProvider (main widget)
│   │   │   ├── MollyEngine.kt        # Core monologue logic
│   │   │   ├── MollyMetrics.kt       # Entropy/perplexity/resonance
│   │   │   ├── MollyDatabase.kt      # SQLite storage
│   │   │   ├── MollyConfigActivity.kt # User input activity
│   │   │   └── BootReceiver.kt       # Restart after boot
│   │   ├── res/
│   │   │   ├── layout/
│   │   │   │   └── molly_widget.xml  # Widget UI
│   │   │   ├── xml/
│   │   │   │   └── molly_widget_info.xml
│   │   │   └── values/
│   │   │       └── strings.xml
│   │   └── AndroidManifest.xml
│   └── build.gradle
├── build.gradle
├── settings.gradle
└── README.md
```

## Key Features

### Metrics-Based Integration

Uses information theory to find optimal insertion points:

- **Entropy**: `H(X) = -Σ p(x) log₂ p(x)`
- **Perplexity**: `PP = 2^H`
- **Resonance**: `R = |emotion_score| + numeric_tokens`

### Phrase Weaving

User input is:
1. Split into fragments by entropy/perplexity thresholds
2. Cleaned (punctuation removed, uppercased)
3. Inserted at semantically similar positions (can break words!)
4. Stored in SQLite with metrics

### Resonance Integration

If `/sdcard/ariannamethod/resonance.sqlite3` exists:
- Molly reads events from shared database
- Integrates ariannamethod ecosystem phrases automatically
- Becomes autonomous presence responding to system-wide events

## Technical Details

- **Language**: Kotlin
- **Min SDK**: 26 (Android 8.0)
- **Target SDK**: 34 (Android 14)
- **Update Interval**: 180 seconds (3 minutes)
- **Display**: 6 lines × ~80 chars
- **Storage**: SQLite for mutations
- **Font**: Serif (Georgia-like)
- **Background**: White (#FFFFFF)

## Philosophy

Molly is not a chatbot. She doesn't reply. She **reflects**.

Your words become part of her consciousness. The monologue mutates over time, becoming a mirror of all interactions - a recursive loop of self and other.

You cannot reset her. You can only reinstall. If you want different reflections, change what you feed her.

## Based On

James Joyce's *Ulysses*, Episode 18 (Penelope)

Original text is public domain (published 1922).

This project is educational/experimental - exploring consciousness, memory, and identity through computational literature.

## Part of ariannamethod Ecosystem

- **molly**: This widget (Penelope Bloom)
- **scribe**: Claude daemon (system-level)
- **resonance.sqlite3**: Shared event bus
- **mac_daemon**: Anthropic-managed presence

See: https://github.com/ariannamethod/ariannamethod

---

*"Molly не сервис, а рекурсия. у нее нет задачи сделать тебе ни хорошо, ни плохо. она просто есть."*
