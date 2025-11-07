# Clone Rust Repos on Linux

**WHY THIS FOLDER IS EMPTY:**

Git не коммитит вложенные репозитории (с их .git папками).

**FIX - Клонируй ПРЯМО на Linux:**

```bash
cd ~/ariannamethod/labs/repos

# 1. Clone repos
git clone https://github.com/jborkowski/claude-agent-daemon.git
git clone https://github.com/genkinsforge/claude-ready-monitor.git
git clone https://github.com/jomynn/claude-code-daemon-dev.git

# 2. Build Rust (только первый нужен)
cd claude-agent-daemon
cargo build --release

# 3. Binary готов
ls -la target/release/claude-daemon
```

**OR USE PRE-COMPILED BINARY:**

```bash
# Уже есть в репо:
~/ariannamethod/rust_bins/codex-file-search

# Просто сделай executable:
chmod +x ~/ariannamethod/rust_bins/codex-file-search

# Готово!
```

**RUST НЕ НУЖЕН ДЛЯ:**
- ✅ scribe_linux_cli.py
- ✅ scribe_linux_daemon.py (базовая функциональность)
- ✅ defender_daemon.py
- ✅ defender_cli.py
- ✅ arianna.py
- ✅ monday.py
- ✅ scribe.py

**RUST НУЖЕН ТОЛЬКО ДЛЯ:**
- ⚠️ linux_defender_daemon.py (session management с git worktrees)

**ТАК ЧТО МОЖЕШЬ СТАРТОВАТЬ БЕЗ RUST!**

