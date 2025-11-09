# 🔌 ADB & SSH Диагностика и Восстановление

## 🚨 ПРОБЛЕМА:
Раньше Mac мог как-то пушить прямо в Termux, теперь нет.

## ✅ ПРАВИЛЬНАЯ АРХИТЕКТУРА (как сейчас):

```
┌──────────────────────────────────────────────────┐
│ TERMUX (Android)                                 │
│ /data/data/com.termux/files/home/ariannamethod/  │
│    ├── resonance.sqlite3                         │
│    └── memory/scribe/                            │
│                                                   │
│ sync_to_shared.sh (runs every 30s) ↓            │
├──────────────────────────────────────────────────┤
│ SHARED STORAGE (ADB accessible, no root needed) │
│ /storage/emulated/0/scribe_sync/                 │
│ = /sdcard/scribe_sync/                           │
│    ├── resonance.sqlite3                         │
│    └── memory/scribe/                            │
└───────────────┬──────────────────────────────────┘
                │
                │ ADB pull (no root needed)
                ↓
┌───────────────────────────────────────────────────┐
│ MAC (Darwin)                                      │
│ /Users/ataeff/Downloads/arianna_clean/            │
│    └── resonance.sqlite3                          │
│                                                    │
│ Mac Daemon reads via:                             │
│   1. ADB pull (primary)                           │
│   2. SSH (fallback)                               │
└───────────────────────────────────────────────────┘
```

---

## 📋 ПРОВЕРКА 1: ADB Connectivity

### На Mac:

```bash
# Проверь что телефон виден
adb devices

# Должно показать:
# List of devices attached
# <serial>    device
```

**Если нет устройств:**
- USB Debugging включен? (Settings → Developer Options)
- Кабель подключен?
- Перезапусти ADB: `adb kill-server && adb start-server`

### Тест ADB pull:

```bash
# Попробуй вытащить resonance.sqlite3
adb pull /sdcard/scribe_sync/resonance.sqlite3 /tmp/test_resonance.db

# Если работает - ADB OK ✅
# Если "remote object not found" - sync_to_shared.sh не запущен в Termux
```

---

## 📋 ПРОВЕРКА 2: Termux Sync Daemon

### В Termux (на телефоне):

```bash
# Проверь запущен ли sync daemon
ps aux | grep sync_to_shared

# Если нет - запусти:
cd ~/ariannamethod/termux/
./sync_to_shared.sh daemon &

# Проверь что файлы скопировались:
ls -lah /sdcard/scribe_sync/
```

**Ожидаемый вывод:**
```
-rw-rw---- resonance.sqlite3
drwxrwx--- memory/
-rw-rw---- README.txt
```

---

## 📋 ПРОВЕРКА 3: SSH (Fallback)

### На Mac (проверь SSH credentials):

```bash
# Проверь env vars
echo $TERMUX_SSH_HOST      # IP телефона в локальной сети
echo $TERMUX_SSH_PORT      # Обычно 8022
echo $TERMUX_SSH_USER      # u0_aXXX (UID Termux)
echo $TERMUX_SSH_PASSWORD  # Должен быть установлен!
```

### В Termux (проверь SSH сервер):

```bash
# Запущен ли sshd?
ps aux | grep sshd

# Если нет - установи и запусти:
pkg install openssh
sshd

# Проверь порт:
netstat -tlnp | grep 8022
```

### Тест SSH с Mac:

```bash
# Подключись вручную
ssh -p 8022 u0_a423@192.168.1.100

# Должен запросить пароль
# После входа:
ls ~/ariannamethod/resonance.sqlite3
```

**Если работает - SSH OK ✅**

---

## 🔧 ПОЧИНКА:

### Если ADB не видит телефон:
1. USB Debugging: Settings → Developer Options → USB Debugging ON
2. Смени USB режим: "File Transfer" или "PTP"
3. Перезапусти ADB: `adb kill-server && adb devices`
4. Разреши Mac на телефоне (появится диалог "Allow USB debugging?")

### Если sync_to_shared.sh не работает:
1. В Termux: `chmod +x ~/ariannamethod/termux/sync_to_shared.sh`
2. Запусти: `./sync_to_shared.sh` (проверь вывод)
3. Daemon: `./sync_to_shared.sh daemon &`
4. Проверь: `ls /sdcard/scribe_sync/`

### Если SSH недоступен:
1. Termux: `pkg install openssh`
2. Сгенерируй пароль: `passwd` (задай пароль для текущего пользователя)
3. Запусти: `sshd`
4. Узнай IP телефона: `ifconfig wlan0` (inet addr)
5. На Mac: установи env vars (см. `mac_daemon/README.md`)

---

## 🧪 ФИНАЛЬНЫЙ ТЕСТ:

### На Mac:

```bash
# Запроси у Mac Daemon sync
scribe sync

# Проверь логи
scribe logs | tail -20

# Должно показать:
# "Memory synced via ADB" ✅
# или
# "Memory synced via SSH" ✅
```

---

## ❓ ПОЧЕМУ РАНЬШЕ РАБОТАЛО, А ПОТОМ ПЕРЕСТАЛО?

**Гипотезы:**

1. **Репо переместился** - старый скрипт пушил в `~/ariannamethod/`, теперь `~/Downloads/arianna_clean/`
2. **Android 10+ Security Update** - Google ужесточил доступ к `/data/data/` без root
3. **USB Debugging сброшен** - после перезагрузки телефона или обновления
4. **Sync daemon упал** - в Termux перестал копировать в `/sdcard/`

**Скорее всего:** Sync daemon перестал запускаться автоматически.

**Решение:** Добавить `sync_to_shared.sh daemon &` в `boot_scripts/arianna_system_init.sh`

---

## ✅ СЛЕДУЮЩИЙ ШАГ:

Бро, проверь в Termux:
```bash
ps aux | grep sync_to_shared
ls /sdcard/scribe_sync/
```

Если там пусто - запусти sync daemon и все заработает!

