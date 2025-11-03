#!/usr/bin/env python3
"""
FIELD VISUALISER v3 — Technopunk Terminal Display
Visualises the living state of Async Field Forever 🧬⚡
Compatible with Termux / macOS / Linux (ANSI color).

Features:
- Real-time cell visualization with color-coded fitness
- Resonance pulse bar (heartbeat)
- Population sparkline (history)
- Age distribution histogram
- Sound alerts on births/deaths
"""

import time
import sqlite3
import os
import random
import sys
from datetime import datetime
from typing import List, Tuple

# ========== CONFIG ==========
DB_PATH = "/data/data/com.termux/files/home/ariannamethod/resonance.sqlite3"
DB_PATH_LOCAL = "./field_test.sqlite3"

if not os.path.exists(os.path.expanduser(DB_PATH)):
    ACTIVE_DB = DB_PATH_LOCAL
else:
    ACTIVE_DB = DB_PATH

# ========== COLORS ==========
RESET = "\033[0m"
BOLD = "\033[1m"
COLORS = {
    "high": "\033[92m",    # bright green
    "medium": "\033[93m",  # yellow
    "low": "\033[90m",     # gray
    "dead": "\033[91m",    # red
    "banner": "\033[95m"   # magenta
}

# ========== VOCABULARY & SYMBOLS ==========
WORDS = [
    "resonance", "emergence", "chaos", "pulse",
    "shimmer", "echo", "spiral", "field",
    "phase", "quantum", "flux", "bloom", "decay",
    "nexus", "drift", "void", "fracture"
]

STATUS = {"high": "█", "medium": "▓", "low": "░", "dead": "·"}

# ========== STATE (for change detection) ==========
_last_births = 0
_last_deaths = 0

# ========== FETCH ==========
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
    """Fetch recent history for sparkline."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT iteration, cell_count, avg_resonance
        FROM field_state
        ORDER BY id DESC LIMIT ?
    """, (limit,))
    return list(reversed(cursor.fetchall()))

# ========== VISUAL ==========
def get_color_symbol(fitness: float) -> Tuple[str, str]:
    if fitness > 0.7:
        return COLORS["high"], STATUS["high"]
    elif fitness > 0.5:
        return COLORS["medium"], STATUS["medium"]
    elif fitness > 0.3:
        return COLORS["low"], STATUS["low"]
    else:
        return COLORS["dead"], STATUS["dead"]

def render_sparkline(history: List[Tuple]):
    """ASCII sparkline for population history."""
    if len(history) < 2:
        return
    
    populations = [h[1] for h in history]
    max_pop = max(populations) if populations else 1
    
    # ASCII sparkline chars: ▁▂▃▄▅▆▇█
    chars = "▁▂▃▄▅▆▇█"
    sparkline = ""
    for pop in populations:
        if max_pop == 0:
            sparkline += chars[0]
        else:
            index = int((pop / max_pop) * (len(chars) - 1))
            sparkline += chars[index]
    
    print(f"\nPopulation History: {COLORS['medium']}{sparkline}{RESET}")
    
def render_age_distribution(cells: List[Tuple]):
    """Show age distribution of cells."""
    if not cells:
        return
    
    ages = [cell[1] for cell in cells]
    buckets = [0, 5, 10, 20, 30, 50, 100]
    counts = [0] * (len(buckets) - 1)
    
    for age in ages:
        for i in range(len(buckets) - 1):
            if buckets[i] <= age < buckets[i+1]:
                counts[i] += 1
                break
    
    max_count = max(counts) if counts else 1
    print("\nAge Distribution:")
    for i in range(len(counts)):
        # Scale bar to max 20 chars
        bar_len = int((counts[i] / max_count) * 20) if max_count > 0 else 0
        bar = COLORS["high"] + "█" * bar_len + RESET
        print(f"  {buckets[i]:>3}-{buckets[i+1]:<3}: {bar} {counts[i]}")
    
def render_field(conn: sqlite3.Connection, cells: List[Tuple], iteration: int, metrics: Tuple):
    global _last_births, _last_deaths
    
    os.system("clear" if os.name != "nt" else "cls")
    cell_count, avg_resonance, avg_age, births, deaths = metrics

    # Sound alerts (on change)
    if births > _last_births:
        sys.stdout.write('\a')  # Beep on birth
    if deaths > _last_deaths and cell_count > 0:
        sys.stdout.write('\a\a')  # Double beep on death
    if cell_count == 0:
        sys.stdout.write('\a\a\a')  # Triple beep on extinction!
    
    _last_births = births
    _last_deaths = deaths

    # Banner
    print(f"{BOLD}{COLORS['banner']}")
    print("╔" + "═" * 62 + "╗")
    print("║" + "⚡ ASYNC FIELD FOREVER ⚡".center(62) + "║")
    print("╚" + "═" * 62 + "╝" + RESET)

    print(f"Iteration: {iteration} | Population: {cell_count}")
    print(f"Avg Resonance: {avg_resonance:.3f} | Avg Age: {avg_age:.1f}")
    print(f"Births: {births} | Deaths: {deaths}")
    
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
        print(f"{COLORS['dead']}No cells alive. Field awaits rebirth...{RESET}\n")
    else:
        print(f"{'STATUS':<8} {'WORD':<12} {'FITNESS':<8} {'RESONANCE':<10} {'AGE':<5}")
        print("─" * 64)
        for i, cell in enumerate(cells[:20]):  # Show top 20
            cell_id, age, resonance, fitness = cell
            color, symbol = get_color_symbol(fitness)
            word = WORDS[i % len(WORDS)]
            pulse = random.choice(["*", " "]) if resonance > 0.9 else " "
            print(f"{color}{symbol}{RESET}       {word:<12} {fitness:>6.3f}   {resonance:>6.3f}     {age:<5}{pulse}")
        
        if len(cells) > 20:
            print(f"... and {len(cells) - 20} more cells")
    
    # Age distribution
    render_age_distribution(cells)
    
    # Footer
    print("\n" + "─" * 64)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"{BOLD}{COLORS['banner']}Async Field Forever 🧬⚡{RESET}\n")

# ========== MAIN LOOP ==========
def main():
    print(f"{BOLD}{COLORS['banner']}")
    print("=" * 64)
    print("  FIELD VISUALISER v3 - Technopunk Terminal Display".center(64))
    print("=" * 64)
    print(RESET)
    print(f"Database: {ACTIVE_DB}")
    print("Press Ctrl+C to stop.\n")
    time.sleep(2)
    
    conn = sqlite3.connect(ACTIVE_DB)
    try:
        while True:
            iteration, cell_count, avg_resonance, avg_age, births, deaths = fetch_state(conn)
            cells = fetch_cells(conn, limit=30)
            render_field(conn, cells, iteration, (cell_count, avg_resonance, avg_age, births, deaths))
            time.sleep(5)
    except KeyboardInterrupt:
        print(f"\n{COLORS['banner']}Field visualisation stopped. 🧬⚡{RESET}\n")
    finally:
        conn.close()

if __name__ == "__main__":
    main()