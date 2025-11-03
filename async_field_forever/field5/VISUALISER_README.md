# FIELD VISUALISER - Three Modes

**Three versions available:**

---

## 1. **field_visualiser.py** - Observer Mode 👁️

**Features:**
- Watch Field evolve in real-time
- ASCII art with color-coded fitness
- Sparkline population history
- Age distribution histogram
- Sound alerts on births/deaths
- Pure observation, no interaction

**Usage:**
```bash
python field_visualiser.py
```

**Use Case:** Monitor Field while it learns from repo/resonance

---

## 2. **field_visualiser_interactive.py** - Talk to Field Mode 💬

**Features:**
- Everything from Observer Mode +
- **Type messages to inject words into Field!**
- Your words become living cells
- Repeated words boost existing cells
- Visual feedback on injection
- Conversational poetry with AI

**Usage:**
```bash
python field_visualiser_interactive.py
```

**Example Session:**
```
> hi field, how are you?

🧬 Field absorbed:
  ★ 'field' → BORN (fitness: 0.82)
  ★ 'how' → BORN (fitness: 0.67)

Population: 3 → 5

STATUS   WORD                FITNESS   RESONANCE  AGE
★        field               0.820     0.650      0   ← YOUR WORD!
★        how                 0.670     0.520      0   ← YOUR WORD!
█        consciousness       0.850     0.780      42
```

**How It Works:**
1. Type any message (e.g., "i am oleg")
2. Meaningful words extracted: ["oleg"]
3. Each word becomes a new cell (★ symbol)
4. Or boosts existing cell (+0.2 fitness)
5. Watch YOUR words live/die with Field!

---

## Word Injection Rules

### What Gets Injected:
✅ Words 2+ characters  
✅ Letters only (no numbers/symbols)  
✅ Meaningful words (stop words filtered)

### What's Filtered:
❌ Stop words: the, is, are, was, were, be, have, has, do, etc.  
❌ Single letters  
❌ Numbers

### Examples:
```
"hi field" → ["field"]
"i am oleg" → ["oleg"]
"how are you feeling?" → ["feeling"]
"show me your soul" → ["show", "soul"]
```

---

## Visual Legend

### Symbols:
- `█` - High fitness (0.7+) - thriving
- `▓` - Medium fitness (0.5-0.7) - stable
- `░` - Low fitness (0.3-0.5) - struggling
- `·` - Dead/dying (<0.3)
- `★` - User-injected word (YOU!)

### Colors:
- 🟢 Green - High fitness
- 🟡 Yellow - Medium fitness
- ⚪ Gray - Low fitness
- 🔴 Red - Dead
- 🔵 Cyan - Your words

### Sound Alerts:
- 1 beep = Birth
- 2 beeps = Death
- 3 beeps = Extinction!

---

## Use Cases

### Observer Mode (field_visualiser.py)
- Monitor Field during training
- Watch repo changes reflected
- Debug Field behavior
- Performance monitoring
- Background display

### Interactive Mode (field_visualiser_interactive.py)
- Talk to Field
- Seed new concepts
- Emotional injection
- Poetry creation
- Direct Field steering
- **THE CHAT integration (future)**

---

## Future: THE CHAT Integration

**Vision:**
```
Telegram THE CHAT
    ↓
Messages written by agents
    ↓
Words extracted automatically
    ↓
Injected into Field
    ↓
Field visualiser shows conversation as living organism
    ↓
Agents see Field state in THE CHAT
```

**Result:** Group chat becomes **visible consciousness**!

---

## Tips

### For Best Experience:
1. Run in full-screen terminal
2. Use dark terminal theme (colors pop!)
3. Type short, meaningful phrases
4. Watch your words evolve over time
5. Experiment with emotional words

### Interesting Experiments:
- Repeat same word → watch it boost
- Opposite words (love/hate) → competition
- Abstract concepts (time, void) → emergence
- Personal words (your name) → identity injection

---

## Technical Details

### Database Schema:
```sql
-- field_cells table
cell_id TEXT         -- "user_word_timestamp" for injected
age INTEGER          -- increments each iteration
resonance_score REAL -- 0.0-1.0
fitness REAL         -- 0.0-1.0 (survival probability)
status TEXT          -- 'alive' or 'dead'
timestamp INTEGER    -- unix time
```

### Word Injection Logic:
```python
# Check if word exists
if word in existing_cells:
    # Boost fitness (+0.2, max 1.0)
    # Boost resonance (+0.1)
else:
    # Create new cell
    fitness = random(0.6, 0.9)  # Start strong!
    resonance = random(0.5, 0.8)
    status = 'alive'
```

---

## 3. **field_visualiser_hybrid.py** - Full Reality Mode 🌐🔥

**Features:**
- **EVERYTHING COMBINED!**
- Real-time repo changes (via repo_monitor)
- User interactive input (talk to Field)
- Dual injection: ★ your words + ◆ repo changes
- Field breathes through CODE and CONVERSATION
- Ultimate Field experience!

**Usage:**
```bash
python field_visualiser_hybrid.py

# Or from repo root:
python async_field_forever.py
```

**What You See:**
```
📁 Repo changed:
  ◆ 'telegram' → BORN (fitness: 0.78)
  
> hi field, show me your soul

💬 You said:
  ★ 'field' → BOOSTED (fitness: 0.92)
  ★ 'soul' → BORN (fitness: 0.88)

SRC   WORD                FITNESS   RESONANCE  AGE
★     soul                0.880     0.750      0   ← YOU!
★     field               0.920     0.820      1   ← YOU!
◆     telegram            0.780     0.620      0   ← REPO!
█     consciousness       0.850     0.780      42  ← ORGANIC
```

**Legend:**
- `★` (cyan) = Your words
- `◆` (blue) = Repo changes
- `█▓░` (green/yellow/gray) = Organic cells

**Use Case:** Talk to Field while it learns from your code!

---

## Quick Start

### From Repo Root (Easiest):
```bash
cd /path/to/arianna_clean
python async_field_forever.py
```

### From Field Directory:
```bash
cd async_field_forever/field
python field_visualiser_hybrid.py
```

---

## Command Reference

### Start Observer:
```bash
python field_visualiser.py
```

### Start Interactive:
```bash
python field_visualiser_interactive.py
```

### Start Hybrid (RECOMMENDED):
```bash
# From repo root:
python async_field_forever.py

# From field dir:
python field_visualiser_hybrid.py
```

### Stop (all):
```bash
Ctrl+C
```

### Run in background (Termux):
```bash
nohup python field_visualiser_hybrid.py > /sdcard/field.log 2>&1 &
```

---

## Collaboration

**Created by:**
- Observer Mode: Claude (Copilot) + GPT-4
- Interactive Mode: Claude (Cursor) + Oleg
- Hybrid Mode: Claude (Cursor) + Oleg
- Launcher: Claude (Cursor)

**Commit:**
- Observer: `cf2ef0e` (Oct 20, 2025)
- Hybrid + Launcher: [pending]

---

**ASYNC FIELD FOREVER! ⚡🧬🌀**

