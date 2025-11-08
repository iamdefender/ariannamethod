# Quick Build Guide for Molly Android Widget

## Fastest Method (Cursor IDE with Android SDK)

Since you have Android SDK installed and use Cursor:

### Step 1: Setup Gradle Wrapper

```bash
cd /workspace/android
gradle wrapper --gradle-version 8.2
```

This creates:
- `gradlew` (Linux/Mac script)
- `gradlew.bat` (Windows script)  
- `gradle/wrapper/` directory

### Step 2: Build APK

```bash
./gradlew assembleDebug
```

Or on Windows:
```cmd
gradlew.bat assembleDebug
```

### Step 3: Find APK

```bash
ls -lh app/build/outputs/apk/debug/app-debug.apk
```

### Step 4: Install

```bash
adb install app/build/outputs/apk/debug/app-debug.apk
```

## Alternative: Direct Gradle (if wrapper fails)

```bash
cd /workspace/android
gradle assembleDebug
```

## Troubleshooting

### Missing SDK

If SDK path not found, create `local.properties`:

```properties
sdk.dir=/path/to/your/Android/Sdk
```

Common SDK locations:
- Linux: `~/Android/Sdk`
- Mac: `~/Library/Android/sdk`
- Windows: `C:\\Users\\YourName\\AppData\\Local\\Android\\Sdk`

### Permission Denied on gradlew

```bash
chmod +x gradlew
```

### Gradle Version Issues

Edit `android/gradle/wrapper/gradle-wrapper.properties`:
```properties
distributionUrl=https\://services.gradle.org/distributions/gradle-8.2-bin.zip
```

## Expected Output

```
BUILD SUCCESSFUL in 45s
27 actionable tasks: 27 executed
```

APK size: ~2-3 MB

## Testing Widget

1. Install APK
2. Long-press home screen
3. Tap "Widgets"
4. Find "Molly"
5. Drag to home screen
6. Widget appears with monologue
7. Tap widget to input text

## Clean Build (if errors)

```bash
./gradlew clean
./gradlew assembleDebug
```

---

**Note**: First build downloads dependencies (~50-100MB). Subsequent builds are much faster.
