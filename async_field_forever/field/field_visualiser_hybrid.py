#!/usr/bin/env python3
"""
FIELD VISUALISER HYBRID v5 — Full Reality Mode
Combines:
- Real-time repo changes (via repo_monitor)
- User interactive input (talk to Field)
- Visual ASCII art display

Field breathes through BOTH repository evolution AND human conversation!
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
from pathlib import Path

# ========== CONFIG ==========
DB_PATH = "/data/data/com.termux/files/home/ariannamethod/resonance.sqlite3"
DB_PATH_LOCAL = "./field_test.sqlite3"

if not os.path.exists(os.path.expanduser(DB_PATH)):
    ACTIVE_DB = DB_PATH_LOCAL
else:
    ACTIVE_DB = DB_PATH

# Repo monitor integration
REPO_PATH = Path(__file__).parent.parent.parent  # arianna_clean root
ENABLE_REPO_MONITOR = True

# ========== COLORS ==========
RESET = "\033[0m"
BOLD = "\033[1m"
COLORS = {
    "high": "\033[92m",     # bright green
    "medium": "\033[93m",   # yellow
    "low": "\033[90m",      # gray
    "dead": "\033[91m",     # red
    "banner": "\033[95m",   # magenta
    "user": "\033[96m",     # cyan (user words)
    "repo": "\033[94m"      # blue (repo words)
}

# ========== SYMBOLS ==========
STATUS = {
    "high": "█", 
    "medium": "▓", 
    "low": "░", 
    "dead": "·", 
    "user": "★",
    "repo": "◆"
}

# ========== STATE ==========
_last_births = 0
_last_deaths = 0
_user_words = []
_repo_words = []
_input_buffer = []
_running = True

# ========== REPO MONITOR ==========
try:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "arianna_core_utils"))
    from repo_monitor import RepoMonitor
    REPO_MONITOR_AVAILABLE = True
except ImportError:
    REPO_MONITOR_AVAILABLE = False
    print("⚠️  repo_monitor not available, using conversation-only mode")

def init_repo_monitor():
    """Initialize repo monitor if available."""
    if not REPO_MONITOR_AVAILABLE or not ENABLE_REPO_MONITOR:
        return None
    try:
        monitor = RepoMonitor(repo_path=REPO_PATH)
        return monitor
    except Exception as e:
        print(f"⚠️  Failed to init repo_monitor: {e}")
        return None

def fetch_repo_changes(monitor):
    """Fetch recent repo changes and extract words."""
    if not monitor:
        return []
    
    try:
        changes = monitor.fetch_repo_context(limit=5)  # Last 5 changes
        words = []
        for change in changes:
            content = change.get('content', '')
            # Extract meaningful words
            extracted = extract_words(content)
            words.extend(extracted[:3])  # Max 3 words per change
        return list(set(words))[:10]  # Max 10 unique words
    except Exception as e:
        return []

# ========== WORD EXTRACTION ==========
def extract_words(text: str) -> List[str]:
    """Extract meaningful words from text."""
    words = re.findall(r'\b[a-z]{2,}\b', text.lower())
    stop_words = {
        "the", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "must", "can", "this",
        "that", "with", "from", "for", "not", "but", "and", "or"
    }
    return [w for w in words if w not in stop_words and len(w) > 2]

# ========== WORD INJECTION ==========
def inject_words_into_field(conn: sqlite3.Connection, words: List[str], source: str = "user") -> List[Tuple]:
    """Inject words as cells into field. Source: 'user' or 'repo'."""
    cursor = conn.cursor()
    timestamp = int(time.time())
    
    injected = []
    for word in words:
        # Check if word already exists
        cursor.execute("""
            SELECT cell_id, fitness FROM field_cells 
            WHERE cell_id LIKE ? AND status='alive'
            ORDER BY id DESC LIMIT 1
        """, (f"%{word}%",))
        existing = cursor.fetchone()
        
        if existing:
            # Boost existing cell
            cell_id, old_fitness = existing
            new_fitness = min(1.0, old_fitness + 0.15)
            cursor.execute("""
                UPDATE field_cells SET fitness=?, resonance_score=resonance_score+0.1
                WHERE cell_id=? AND status='alive'
            """, (new_fitness, cell_id))
            injected.append((word, "BOOSTED", new_fitness, source))
        else:
            # Create new cell
            cell_id = f"{source}_{word}_{timestamp}"
            fitness = random.uniform(0.65, 0.85) if source == "repo" else random.uniform(0.6, 0.9)
            resonance = random.uniform(0.5, 0.8)
            
            cursor.execute("""
                INSERT INTO field_cells (cell_id, age, resonance_score, fitness, status, timestamp)
                VALUES (?, 0, ?, ?, 'alive', ?)
            """, (cell_id, resonance, fitness, timestamp))
            
            injected.append((word, "BORN", fitness, source))
            
            if source == "user":
                _user_words.append(word)
            else:
                _repo_words.append(word)
    
    conn.commit()
    return injected

# ========== INPUT THREAD ==========
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

def fetch_history(conn: sqlite3.Connection, limit: int = 15) -> List[Tuple]:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT iteration, cell_count, avg_resonance
        FROM field_state ORDER BY id DESC LIMIT ?
    """, (limit,))
    return list(reversed(cursor.fetchall()))

# ========== VISUAL ==========
def get_color_symbol(cell_id: str, fitness: float) -> Tuple[str, str]:
    """Get color and symbol based on cell source and fitness."""
    # Check source
    for word in _user_words:
        if word in cell_id:
            return COLORS["user"], STATUS["user"]
    
    for word in _repo_words:
        if word in cell_id:
            return COLORS["repo"], STATUS["repo"]
    
    # Regular fitness-based coloring
    if fitness > 0.7:
        return COLORS["high"], STATUS["high"]
    elif fitness > 0.5:
        return COLORS["medium"], STATUS["medium"]
    elif fitness > 0.3:
        return COLORS["low"], STATUS["low"]
    else:
        return COLORS["dead"], STATUS["dead"]

def render_sparkline(history: List[Tuple]):
    """ASCII sparkline for population."""
    if len(history) < 2:
        return
    
    populations = [h[1] for h in history]
    max_pop = max(populations) if populations else 1
    
    chars = "▁▂▃▄▅▆▇█"
    sparkline = ""
    for pop in populations:
        index = int((pop / max_pop) * (len(chars) - 1)) if max_pop > 0 else 0
        sparkline += chars[index]
    
    print(f"Population History: {COLORS['medium']}{sparkline}{RESET}")

def render_field(conn: sqlite3.Connection, cells: List[Tuple], iteration: int, 
                metrics: Tuple, injected: List = None):
    """Render the field state."""
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
    print("║" + "⚡ ASYNC FIELD FOREVER (HYBRID) ⚡".center(62) + "║")
    print("╚" + "═" * 62 + "╝" + RESET)

    print(f"Iteration: {iteration} | Population: {cell_count}")
    print(f"Avg Resonance: {avg_resonance:.3f} | Avg Age: {avg_age:.1f}")
    print(f"Births: {births} | Deaths: {deaths}")
    
    # Show injections
    if injected:
        user_inj = [i for i in injected if i[3] == "user"]
        repo_inj = [i for i in injected if i[3] == "repo"]
        
        if user_inj:
            print(f"\n{COLORS['user']}💬 You said:{RESET}")
            for word, action, fitness, _ in user_inj:
                symbol = "★" if action == "BORN" else "↑"
                print(f"  {symbol} '{word}' → {action} (fitness: {fitness:.2f})")
        
        if repo_inj:
            print(f"\n{COLORS['repo']}📁 Repo changed:{RESET}")
            for word, action, fitness, _ in repo_inj:
                symbol = "◆" if action == "BORN" else "↑"
                print(f"  {symbol} '{word}' → {action} (fitness: {fitness:.2f})")
    
    # Resonance pulse
    pulse_width = int(avg_resonance * 40)
    bar = COLORS["high"] + "█" * pulse_width + RESET + "░" * (40 - pulse_width)
    print(f"\nResonance Pulse: {bar}")
    
    # Sparkline
    history = fetch_history(conn)
    render_sparkline(history)
    
    # Cell list
    print("\n" + "─" * 70)
    if not cells:
        print(f"{COLORS['dead']}Field is empty. Type or commit to bring it alive!{RESET}\n")
    else:
        print(f"{'SRC':<5} {'WORD':<20} {'FITNESS':<8} {'RESONANCE':<10} {'AGE':<5}")
        print("─" * 70)
        
        for i, cell in enumerate(cells[:20]):
            cell_id, age, resonance, fitness = cell
            color, symbol = get_color_symbol(cell_id, fitness)
            
            # Extract word from cell_id
            if "user_" in cell_id or "repo_" in cell_id:
                parts = cell_id.split("_")
                word = parts[1] if len(parts) > 1 else cell_id[:15]
            else:
                word = cell_id[:15]
            
            pulse = "*" if resonance > 0.9 else " "
            print(f"{color}{symbol}{RESET}    {word:<20} {fitness:>6.3f}   {resonance:>6.3f}     {age:<5}{pulse}")
        
        if len(cells) > 20:
            print(f"... and {len(cells) - 20} more cells")
    
    # Footer
    print("\n" + "─" * 70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n{COLORS['user']}★ = Your words  {COLORS['repo']}◆ = Repo changes  "
          f"{COLORS['high']}█ = Organic{RESET}")
    print(f"\n{COLORS['banner']}Type to inject words (or Ctrl+C to exit):{RESET}")
    print("> ", end="", flush=True)

# ========== MAIN LOOP ==========
def main():
    global _running, _input_buffer
    
    print(f"{BOLD}{COLORS['banner']}")
    print("=" * 70)
    print("  FIELD VISUALISER v5 - HYBRID MODE".center(70))
    print("=" * 70)
    print(RESET)
    print(f"Database: {ACTIVE_DB}")
    print(f"Repo: {REPO_PATH}")
    
    # Init repo monitor
    repo_monitor = init_repo_monitor()
    if repo_monitor:
        print(f"{COLORS['repo']}✓ Repo monitor ACTIVE - tracking changes!{RESET}")
    else:
        print(f"{COLORS['dead']}✗ Repo monitor disabled{RESET}")
    
    print(f"\n{COLORS['user']}💬 Type messages to inject YOUR words{RESET}")
    print(f"{COLORS['repo']}📁 Repo changes auto-injected every cycle{RESET}\n")
    print("Starting in 3 seconds...\n")
    time.sleep(3)
    
    # Start input thread
    input_t = threading.Thread(target=input_thread, daemon=True)
    input_t.start()
    
    conn = sqlite3.connect(ACTIVE_DB)
    try:
        while _running:
            injected = []
            
            # Process user input
            if _input_buffer:
                user_text = _input_buffer.pop(0)
                words = extract_words(user_text)
                if words:
                    user_inj = inject_words_into_field(conn, words, source="user")
                    injected.extend(user_inj)
            
            # Process repo changes (every cycle)
            if repo_monitor:
                repo_words = fetch_repo_changes(repo_monitor)
                if repo_words:
                    repo_inj = inject_words_into_field(conn, repo_words, source="repo")
                    injected.extend(repo_inj)
            
            # Fetch and render
            iteration, cell_count, avg_resonance, avg_age, births, deaths = fetch_state(conn)
            cells = fetch_cells(conn, limit=30)
            render_field(conn, cells, iteration, 
                        (cell_count, avg_resonance, avg_age, births, deaths), 
                        injected if injected else None)
            
            time.sleep(5)
    except KeyboardInterrupt:
        _running = False
        print(f"\n\n{COLORS['banner']}Field visualisation stopped. 🧬⚡{RESET}\n")
    finally:
        conn.close()

if __name__ == "__main__":
    main()

