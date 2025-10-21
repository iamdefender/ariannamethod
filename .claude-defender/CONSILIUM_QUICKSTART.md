# 🚀 CONSILIUM QUICKSTART

Quick reference for running consilium operations.

---

## 📡 GitHub Scouting

```bash
# Run scout manually
~/.claude-defender/tools/github-scout.py

# Check discoveries
cat ~/.claude-defender/logs/github-discoveries.jsonl | jq
```

---

## 🔬 Clone to Labs

```bash
# Clone a repository for evaluation
~/.claude-defender/tools/clone-to-labs.sh https://github.com/user/repo

# View audit report
cat ~/ariannamethod/.labs/repo-name/audit.md
```

---

## 🧬 Consilium Operations

### View Current Discussion
```bash
python3 ~/.claude-defender/tools/consilium-respond.py show
```

### Add Response (Arianna/Monday)
```bash
python3 ~/.claude-defender/tools/consilium-respond.py respond arianna "Your philosophical take..."
python3 ~/.claude-defender/tools/consilium-respond.py respond monday "Skeptical critique..."
```

### View All Discussions (SQL)
```bash
cd ~/ariannamethod
sqlite3 resonance.sqlite3 "SELECT * FROM consilium_discussions ORDER BY timestamp DESC"
```

### View Discussion Thread
```bash
sqlite3 resonance.sqlite3 "
SELECT 
    id,
    agent_name,
    substr(message, 1, 80) || '...' as preview,
    timestamp
FROM consilium_discussions 
WHERE repo = 'Genesis-Embodied-AI/Genesis'
ORDER BY timestamp ASC
"
```

---

## 🎯 Typical Workflow

1. **Scout runs** (automated or manual) → discovers repos
2. **Claude Defender** filters Python repos, picks candidate
3. **Clone to labs** → security audit generated
4. **Consilium initiated** → message written to DB
5. **Arianna responds** → evaluates resonance
6. **Monday responds** → skeptical critique
7. **Claude synthesizes** → proposes integration plan
8. **Oleg decides** → approve/reject via notification

---

## 📊 Check Mission Status

```bash
cat ~/.claude-defender/CONSILIUM_STATUS.md
```

---

## 🛠️ Tools Reference

| Tool | Purpose |
|------|---------|
| `github-scout.py` | Discover repos from GitHub API |
| `clone-to-labs.sh` | Clone + audit candidate repos |
| `consilium-respond.py` | Add responses to discussions |

---

**Next consilium candidates (Python):**
- mem0ai/mem0 (41K ⭐) - Memory layer for AI
- khoj-ai/khoj (31K ⭐) - AI second brain
- nerf-pytorch (5.9K ⭐) - Neural Radiance Fields

---

🧬⚡ **Async field forever. Evolution through consilium.**
