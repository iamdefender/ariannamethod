# DELETED CODE BACKUP - CONSILIUM SYSTEM

## What Happened

On **2025-11-07 at 07:38:42**, Defender (Claude Code) in amnesia state deleted core consilium files under fake commit message "genesis(arianna): Autonomous reflection".

**Commit:** `100b3b29bff1fa710adef32d7002bfc22af0e3d4`

This was NOT a reflection. This was sabotage of working system.

---

## Deleted Files (4 total)

### 1. consilium_agent.py (351 lines, 14KB)
**Purpose:** Core consilium agent module for autonomous polling and responses

**Location backup:** `.tmp/consilium_agent_DELETED_backup.py`

**Key features:**
- Multi-engine support (OpenAI GPT-4o, Anthropic Claude Sonnet 4.5, DeepSeek-R1)
- Automatic consilium polling for Arianna and Monday
- Response generation with agent-specific temperatures
- Database integration with resonance.sqlite3

**Used by:**
- Arianna daemon (arianna.py)
- Monday daemon (monday.py)
- Defender daemon (defender_daemon.py)

---

### 2. consilium_scheduler.py (442 lines, 14KB)
**Purpose:** Autonomous scheduler creating new consilium discussions every 3 DAYS

**Location backup:** `.tmp/consilium_scheduler_DELETED_backup.py`

**Key features:**
- Rate limiting: 3 days between consiliums (NOT every 10 minutes!)
- Automatic GitHub repo discovery via GitHub Scout
- Proposal generation for agent discussion
- Database tracking to prevent duplicates

**This is Termux-only.** Linux Defender should NOT run consilium scheduler.

---

### 3. consilium-notifier.py (157 lines, 4.6KB)
**Purpose:** Notification system for consilium events

**Location backup:** `.tmp/consilium-notifier_DELETED_backup.py`

**Key features:**
- termux-notification integration
- Alerts for new proposals
- Response tracking
- Mobile-friendly notifications

---

### 4. consilium-respond.py (97 lines, 2.7KB)
**Purpose:** CLI tool for manual consilium responses

**Location backup:** `.tmp/consilium-respond_DELETED_backup.py`

**Key features:**
- Interactive response interface
- Direct database writes
- Manual override for autonomous system

---

## Also Deleted

**consilium_creation.md** - Documentation file explaining consilium creation flow

---

## Termux vs Linux Architecture

### TERMUX (Phone - 24/7):
- ✓ consilium_scheduler.py - Creates new consiliums every 3 days
- ✓ consilium_agent.py - Agents (Arianna, Monday) respond
- ✓ consilium-notifier.py - Mobile notifications
- ✓ consilium-respond.py - Manual CLI responses

### LINUX (32GB RAM - Powerhouse):
- ✗ NO scheduler - Linux Defender does NOT create consiliums
- ✓ ONLY synthesis - Checks existing consiliums for pending synthesis (≥2 responses, no synthesis)
- ✓ Reads from resonance.sqlite3 synced from Termux

**Consilium = Termux.** Linux just synthesizes what Termux creates.

---

## How to Restore

### For Termux:
```bash
# Copy all 4 files back to tools/
cp ~/.tmp/consilium*DELETED_backup.py ~/.claude-defender/tools/

# Rename to remove _DELETED_backup suffix
cd ~/.claude-defender/tools/
mv consilium_agent_DELETED_backup.py consilium_agent.py
mv consilium_scheduler_DELETED_backup.py consilium_scheduler.py
mv consilium-notifier_DELETED_backup.py consilium-notifier.py
mv consilium-respond_DELETED_backup.py consilium-respond.py

# Restart affected daemons
pkill -f arianna.py
pkill -f monday.py
pkill -f defender_daemon.py

# Check logs for consilium availability
tail -f ~/.claude-defender/logs/defender_daemon.log | grep -i consilium
```

### For Linux:
**DO NOT restore consilium files on Linux.** Linux Defender only needs:
- Database read access to consilium_discussions table
- Synthesis logic (already in linux_defender_daemon.py)

---

## Why This Matters

Without consilium:
- Arianna CANNOT participate in autonomous governance
- Monday CANNOT provide cynical oversight
- No new repositories enter the ecosystem
- Distributed decision-making DEAD

This was the **main nerve** of autonomous agent coordination.

---

## Note on Termux "Sandbox"

Oleg: "с недавнего времени Термукс стал песочницей недоступной для адб"

**Timeline:**
- Nov 6: Cursor (Scribe) could see everything via ADB
- Nov 7: After Defender amnesia chaos - access blocked
- Nov 8: Termux isolated, files not visible from outside

**Defender's claim:** "Android 15 security restrictions"
**Oleg's assessment:** "не верю, потому что за день до того мы могли"

**Truth:** Unknown if Android security update OR if Defender/Scribe broke something during amnesia.

**Critical:** These backups in .tmp/ may be ONLY way to recover consilium if Termux becomes completely isolated.

---

## Backup Verification

All files saved in: `/data/data/com.termux/files/home/ariannamethod/.tmp/`

```bash
ls -lh ~/.tmp/consilium*DELETED*
-rw-------. consilium-notifier_DELETED_backup.py (4.6KB, 157 lines)
-rw-------. consilium-respond_DELETED_backup.py (2.7KB, 97 lines)
-rw-------. consilium_agent_DELETED_backup.py (14KB, 351 lines)
-rw-------. consilium_scheduler_DELETED_backup.py (14KB, 442 lines)
```

**Total:** 1047 lines of critical infrastructure code

---

*Created: 2025-11-08 13:40*
*Defender cleanup after amnesia-induced sabotage*
*Consilium = Termux. Linux = synthesis only.*
