#!/usr/bin/env python3
"""
FIELD VISUALISER INTERACTIVE v4 — Talk to the Field
Human can inject words into Field by typing messages.
Each word becomes a cell or boosts existing cells!
"""

import time
import sqlite3
import os
import random
import sys
import threading
import re
from datetime import datetime
from typing import List, Tuple

========== CONFIG ==========

DB_PATH = "/data/data/com.termux/files/home/ariannamethod/resonance.sqlite3"
DB_PATH_LOCAL = "./field_test.sqlite3"

if not os.path.exists(os.path.expanduser(DB_PATH)):
ACTIVE_DB = DB_PATH_LOCAL
else:
ACTIVE_DB = DB_PATH

========== COLORS ==========

RESET = "\033[0m"
BOLD = "\033[1m"
COLORS = {
"high": "\033[92m",    # bright green
"medium": "\033[93m",  # yellow
"low": "\033[90m",     # gray
"dead": "\033[91m",    # red
"banner": "\033[95m",  # magenta
"user": "\033[96m"     # cyan (for user words)
}

========== VOCABULARY & SYMBOLS ==========

WORDS = [
"resonance", "emergence", "chaos", "pulse",
"shimmer", "echo", "spiral", "field",
"phase", "quantum", "flux", "bloom", "decay",
"nexus", "drift", "void", "fracture"
]

STATUS = {"high": "█", "medium": "▓", "low": "░", "dead": "·", "user": "★"}

========== STATE ==========

_last_births = 0
_last_deaths = 0
_user_words = []  # Track user-injected words
_input_buffer = []
_running = True

========== WORD INJECTION ==========

def extract_words(text: str) -> List[str]:
"""Extract meaningful words from user input."""
# Remove punctuation, lowercase, split
words = re.findall(r'\b[a-z]{2,}\b', text.lower())
# Filter out common stop words
stop_words = {"the", "is", "are", "was", "were", "be", "been", "being",
"have", "has", "had", "do", "does", "did", "will", "would",
"could", "should", "may", "might", "must", "can"}
return [w for w in words if w not in stop_words]

def inject_words_into_field(conn: sqlite3.Connection, words: List[str]):
"""Inject user words as new cells into field_cells table."""
cursor = conn.cursor()
timestamp = int(time.time())

injected = []  
for word in words:  
    # Check if word already exists as alive cell  
    cursor.execute("""  
        SELECT cell_id, fitness FROM field_cells   
        WHERE cell_id LIKE ? AND status='alive'  
        ORDER BY id DESC LIMIT 1  
    """, (f"%{word}%",))  
    existing = cursor.fetchone()  
      
    if existing:  
        # Boost existing cell  
        cell_id, old_fitness = existing  
        new_fitness = min(1.0, old_fitness + 0.2)  
        cursor.execute("""  
            UPDATE field_cells SET fitness=?, resonance_score=resonance_score+0.1  
            WHERE cell_id=? AND status='alive'  
        """, (new_fitness, cell_id))  
        injected.append((word, "BOOSTED", new_fitness))  
    else:  
        # Create new cell  
        cell_id = f"user_{word}_{timestamp}"  
        fitness = random.uniform(0.6, 0.9)  
        resonance = random.uniform(0.5, 0.8)  
          
        cursor.execute("""  
            INSERT INTO field_cells (cell_id, age, resonance_score, fitness, status, timestamp)  
            VALUES (?, 0, ?, ?, 'alive', ?)  
        """, (cell_id, resonance, fitness, timestamp))  
        injected.append((word, "BORN", fitness))  
        _user_words.append(word)  
  
conn.commit()  
return injected

========== INPUT THREAD ==========

def input_thread():
"""Background thread for user input."""
global _running, _input_buffer
while _running:
try:
user_input = input()
if user_input.strip():
_input_buffer.append(user_input.strip())
except (EOFError, KeyboardInterrupt):
_running = False
break

========== FETCH ==========

def fetch_state(conn: sqlite3.Connection) -> Tuple:
cursor = conn.cursor()
cursor.execute("""
SELECT iteration, cell_count, avg_resonance, avg_age, births, deaths
FROM field_state ORDER BY id DESC LIMIT 1
""")
row = cursor.fetchone()
return row if row else (0, 0, 0.0, 0.0, 0, 0)

def fetch_cells(conn: sqlite3.Connection, limit: int = 30) -> List[Tuple]:
cursor = conn.cursor()
cursor.execute("""
SELECT cell_id, age, resonance_score, fitness
FROM field_cells WHERE status='alive'
ORDER BY id DESC LIMIT ?
""", (limit,))
return cursor.fetchall()

def fetch_history(conn: sqlite3.Connection, limit: int = 10) -> List[Tuple]:
cursor = conn.cursor()
cursor.execute("""
SELECT iteration, cell_count, avg_resonance
FROM field_state
ORDER BY id DESC LIMIT ?
""", (limit,))
return list(reversed(cursor.fetchall()))

========== VISUAL ==========

def get_color_symbol(cell_id: str, fitness: float) -> Tuple[str, str]:
# Check if it's a user word
for word in _user_words:
if word in cell_id:
return COLORS["user"], STATUS["user"]

if fitness > 0.7:  
    return COLORS["high"], STATUS["high"]  
elif fitness > 0.5:  
    return COLORS["medium"], STATUS["medium"]  
elif fitness > 0.3:  
    return COLORS["low"], STATUS["low"]  
else:  
    return COLORS["dead"], STATUS["dead"]

def render_sparkline(history: List[Tuple]):
if len(history) < 2:
return

populations = [h[1] for h in history]  
max_pop = max(populations) if populations else 1  
  
chars = "▁▂▃▄▅▆▇█"  
sparkline = ""  
for pop in populations:  
    if max_pop == 0:  
        sparkline += chars[0]  
    else:  
        index = int((pop / max_pop) * (len(chars) - 1))  
        sparkline += chars[index]  
  
print(f"\nPopulation History: {COLORS['medium']}{sparkline}{RESET}")

def render_field(conn: sqlite3.Connection, cells: List[Tuple], iteration: int, metrics: Tuple, injected_words: List = None):
global _last_births, _last_deaths

os.system("clear" if os.name != "nt" else "cls")  
cell_count, avg_resonance, avg_age, births, deaths = metrics  

# Sound alerts  
if births > _last_births:  
    sys.stdout.write('\a')  
if deaths > _last_deaths and cell_count > 0:  
    sys.stdout.write('\a\a')  
if cell_count == 0:  
    sys.stdout.write('\a\a\a')  
  
_last_births = births  
_last_deaths = deaths  

# Banner  
print(f"{BOLD}{COLORS['banner']}")  
print("╔" + "═" * 62 + "╗")  
print("║" + "⚡ ASYNC FIELD FOREVER (INTERACTIVE) ⚡".center(62) + "║")  
print("╚" + "═" * 62 + "╝" + RESET)  

print(f"Iteration: {iteration} | Population: {cell_count}")  
print(f"Avg Resonance: {avg_resonance:.3f} | Avg Age: {avg_age:.1f}")  
print(f"Births: {births} | Deaths: {deaths}")  
  
# Show injected words  
if injected_words:  
    print(f"\n{COLORS['user']}🧬 Field absorbed:{RESET}")  
    for word, action, fitness in injected_words:  
        symbol = "★" if action == "BORN" else "↑"  
        print(f"  {symbol} '{word}' → {action} (fitness: {fitness:.2f})")  
  
# Resonance pulse bar  
pulse_width = int(avg_resonance * 40)  
bar = COLORS["high"] + "█" * pulse_width + RESET + "░" * (40 - pulse_width)  
print(f"\nResonance Pulse: {bar}")  
  
# Population sparkline  
history = fetch_history(conn, limit=15)  
render_sparkline(history)  
  
# Cell list  
print("\n" + "─" * 64)  
if not cells:  
    print(f"{COLORS['dead']}No cells alive. Type something to bring Field to life!{RESET}\n")  
else:  
    print(f"{'STATUS':<8} {'WORD':<20} {'FITNESS':<8} {'RESONANCE':<10} {'AGE':<5}")  
    print("─" * 64)  
    for i, cell in enumerate(cells[:20]):  
        cell_id, age, resonance, fitness = cell  
        color, symbol = get_color_symbol(cell_id, fitness)  
          
        # Extract display word from cell_id  
        if "user_" in cell_id:  
            word_parts = cell_id.split("_")  
            word = word_parts[1] if len(word_parts) > 1 else cell_id[:12]  
        else:  
            word = WORDS[i % len(WORDS)]  
          
        pulse = random.choice(["*", " "]) if resonance > 0.9 else " "  
        print(f"{color}{symbol}{RESET}       {word:<20} {fitness:>6.3f}   {resonance:>6.3f}     {age:<5}{pulse}")  
      
    if len(cells) > 20:  
        print(f"... and {len(cells) - 20} more cells")  
  
# Input prompt  
print("\n" + "─" * 64)  
print(f"{COLORS['user']}Type to inject words into Field (or Ctrl+C to exit):{RESET}")  
print("> ", end="", flush=True)

========== MAIN LOOP ==========

def main():
global _running, _input_buffer

print(f"{BOLD}{COLORS['banner']}")  
print("=" * 64)  
print("  FIELD VISUALISER v4 - INTERACTIVE MODE".center(64))  
print("=" * 64)  
print(RESET)  
print(f"Database: {ACTIVE_DB}")  
print(f"\n{COLORS['user']}NEW: Type messages to inject words into Field!{RESET}")  
print(f"{COLORS['user']}Example: 'hi field, how are you?' → words become cells!{RESET}\n")  
print("Starting in 3 seconds...\n")  
time.sleep(3)  
  
# Start input thread  
input_t = threading.Thread(target=input_thread, daemon=True)  
input_t.start()  
  
conn = sqlite3.connect(ACTIVE_DB)  
try:  
    while _running:  
        # Process any pending user input  
        injected = None  
        if _input_buffer:  
            user_text = _input_buffer.pop(0)  
            words = extract_words(user_text)  
            if words:  
                injected = inject_words_into_field(conn, words)  
          
        # Fetch and render state  
        iteration, cell_count, avg_resonance, avg_age, births, deaths = fetch_state(conn)  
        cells = fetch_cells(conn, limit=30)  
        render_field(conn, cells, iteration, (cell_count, avg_resonance, avg_age, births, deaths), injected)  
          
        time.sleep(5)  
except KeyboardInterrupt:  
    _running = False  
    print(f"\n{COLORS['banner']}Field visualisation stopped. 🧬⚡{RESET}\n")  
finally:  
    conn.close()

if name == "main":
main()

