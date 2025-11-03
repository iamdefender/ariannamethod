#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIELD VISUALISER v6 — Full Grid Hybrid (Termux / macOS / Linux)

Combines:
- Real-time repo changes (via repo_monitor)
- User interactive input (talk to Field)
- Visual ASCII "grid life" with drift & resonance breathing
- Pulse bar, population sparkline, sound alerts

No extra dependencies. Pure ANSI. Safe on dumb terminals (colors can be disabled).
"""

import time
import sqlite3
import os
import random
import sys
import threading
import re
import math
from datetime import datetime
from typing import List, Tuple, Dict
from pathlib import Path
from hashlib import blake2b

# ========== CONFIG ==========
DB_PATH = "/data/data/com.termux/files/home/ariannamethod/resonance.sqlite3"
DB_PATH_LOCAL = "./field_test.sqlite3"

# Auto DB selection
if not os.path.exists(os.path.expanduser(DB_PATH)):
    ACTIVE_DB = DB_PATH_LOCAL
else:
    ACTIVE_DB = DB_PATH

# Repo monitor integration
REPO_PATH = Path(__file__).parent.parent.parent  # repo root (adjust if needed)
ENABLE_REPO_MONITOR = True

# Grid config (tuned for 80x24 and Termux)
GRID_W = 48
GRID_H = 18
GRID_PADDING_TOP = 1
GRID_PADDING_LEFT = 2

# Frame timing (seconds)
FRAME_DT = 0.2    # inner animation step for breathing/drift
UI_REFRESH = 5.0  # how often to refetch DB + re-render UI frame

# Limit rows in lists (short for mobile - keyboard blocks grid)
CELL_LIST_LIMIT = 4

# Banner width (optimized for mobile, 40 fits Termux better)
BANNER_WIDTH = 40

# ========== FLAGS ==========
ENABLE_COLOR = True
ENABLE_SOUND = True  # terminal bell
ENABLE_BREATH = True
ENABLE_DRIFT = True

# ========== COLORS ==========
RESET = "\033[0m" if ENABLE_COLOR else ""
BOLD = "\033[1m" if ENABLE_COLOR else ""
DIM = "\033[2m" if ENABLE_COLOR else ""
COLORS = {
    "high":   "\033[92m" if ENABLE_COLOR else "",  # bright green
    "medium": "\033[93m" if ENABLE_COLOR else "",  # yellow
    "low":    "\033[90m" if ENABLE_COLOR else "",  # gray
    "dead":   "\033[91m" if ENABLE_COLOR else "",  # red
    "banner": "\033[95m" if ENABLE_COLOR else "",  # magenta
    "user":   "\033[96m" if ENABLE_COLOR else "",  # cyan
    "repo":   "\033[94m" if ENABLE_COLOR else "",  # blue
    "white":  "\033[97m" if ENABLE_COLOR else "",
}

# ========== SYMBOLS ==========
STATUS = {
    "high":  "█",
    "med":   "▓",
    "low":   "▒",
    "min":   "░",
    "dead":  "·",
    "user":  "★",
    "repo":  "◆",
    "dot":   "•",
}

# ========== STATE ==========
_last_births = 0
_last_deaths = 0
_user_words: List[str] = []
_repo_words: List[str] = []
_input_buffer: List[str] = []
_running = True

# Animation phase
_breath_phase = 0.0

# ========== REPO MONITOR ==========
try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "arianna_core_utils"))
    from repo_monitor import RepoMonitor
    REPO_MONITOR_AVAILABLE = True
except Exception:
    REPO_MONITOR_AVAILABLE = False

def init_repo_monitor():
    if not REPO_MONITOR_AVAILABLE or not ENABLE_REPO_MONITOR:
        return None
    try:
        return RepoMonitor(repo_path=REPO_PATH)
    except Exception as e:
        print(f"⚠️  Failed to init repo_monitor: {e}")
        return None

def fetch_repo_changes(monitor) -> List[str]:
    if not monitor:
        return []
    try:
        changes = monitor.fetch_repo_context(limit=5)  # last 5 changes
        words = []
        for ch in changes:
            content = ch.get('content', '')
            extracted = extract_words(content)
            words.extend(extracted[:3])  # cap per change
        # return at most 10 unique words
        uniq = []
        seen = set()
        for w in words:
            if w not in seen:
                seen.add(w)
                uniq.append(w)
            if len(uniq) >= 10:
                break
        return uniq
    except Exception:
        return []

# ========== WORD EXTRACTION ==========
STOP_WORDS = {
    "the","is","are","was","were","be","been","being","have","has","had","do","does","did",
    "will","would","could","should","may","might","must","can","this","that","with","from",
    "for","not","but","and","or","into","onto","over","under","between","within","out"
}

def extract_words(text: str) -> List[str]:
    words = re.findall(r'\b[a-z]{2,}\b', text.lower())
    return [w for w in words if w not in STOP_WORDS and len(w) > 2][:32]

# ========== DB INJECTION ==========
def inject_words_into_field(conn: sqlite3.Connection, words: List[str], source: str = "user") -> List[Tuple]:
    """
    Inject words as cells. If word exists as alive cell, boost it.
    Returns list of tuples: (word, action, fitness, source)
    """
    cursor = conn.cursor()
    ts = int(time.time())
    injected = []
    for word in words:
        # check existence
        cursor.execute("""
            SELECT cell_id, fitness FROM field_cells
            WHERE cell_id LIKE ? AND status='alive'
            ORDER BY id DESC LIMIT 1
        """, (f"%{word}%",))
        row = cursor.fetchone()
        if row:
            cell_id, old_fit = row
            new_fit = min(1.0, (old_fit or 0.5) + 0.15)
            cursor.execute("""
                UPDATE field_cells
                SET fitness=?, resonance_score=COALESCE(resonance_score,0)+0.1
                WHERE cell_id=? AND status='alive'
            """, (new_fit, cell_id))
            injected.append((word, "BOOSTED", new_fit, source))
        else:
            # create new
            cell_id = f"{source}_{word}_{ts}"
            fit = random.uniform(0.65, 0.85) if source == "repo" else random.uniform(0.6, 0.9)
            res = random.uniform(0.5, 0.8)
            cursor.execute("""
                INSERT INTO field_cells (cell_id, age, resonance_score, fitness, status, timestamp)
                VALUES (?, 0, ?, ?, 'alive', ?)
            """, (cell_id, res, fit, ts))
            injected.append((word, "BORN", fit, source))
            if source == "user":
                _user_words.append(word)
            else:
                _repo_words.append(word)
    conn.commit()
    return injected

# ========== INPUT THREAD ==========
def input_thread():
    global _running, _input_buffer
    while _running:
        try:
            user_input = input()
            if user_input.strip():
                _input_buffer.append(user_input.strip())
        except (EOFError, KeyboardInterrupt):
            _running = False
            break

# ========== DB FETCH ==========
def fetch_state(conn: sqlite3.Connection) -> Tuple[int,int,float,float,int,int]:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT iteration, cell_count, avg_resonance, avg_age, births, deaths
        FROM field_state ORDER BY id DESC LIMIT 1
    """)
    row = cursor.fetchone()
    if not row:
        return (0,0,0.0,0.0,0,0)
    return row

def fetch_cells(conn: sqlite3.Connection, limit: int = 60) -> List[Tuple[str,int,float,float]]:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cell_id, age, COALESCE(resonance_score,0.0), COALESCE(fitness,0.0)
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

# ========== COLOR/SYMBOL PICK ==========
def is_user_cell(cell_id: str) -> bool:
    return cell_id.startswith("user_") or any(w in cell_id for w in _user_words)

def is_repo_cell(cell_id: str) -> bool:
    return cell_id.startswith("repo_") or any(w in cell_id for w in _repo_words)

def color_and_symbol(cell_id: str, fitness: float) -> Tuple[str, str]:
    # source color/symbol overrides organic
    if is_user_cell(cell_id):
        return COLORS["user"], STATUS["user"]
    if is_repo_cell(cell_id):
        return COLORS["repo"], STATUS["repo"]
    # organic by fitness
    if fitness > 0.75:
        return COLORS["high"], STATUS["high"]
    elif fitness > 0.55:
        return COLORS["medium"], STATUS["med"]
    elif fitness > 0.35:
        return COLORS["low"], STATUS["low"]
    elif fitness > 0.15:
        return COLORS["low"], STATUS["min"]
    else:
        return COLORS["dead"], STATUS["dead"]

# ========== GRID UTILS ==========
def hsh(s: str, mod: int) -> int:
    return int.from_bytes(blake2b(s.encode("utf-8"), digest_size=8).digest(), "little") % max(1,mod)

def base_position(cell_id: str, w: int, h: int) -> Tuple[int,int]:
    # deterministic base idx
    return hsh(cell_id+"_x", w), hsh(cell_id+"_y", h)

def drift_offset(cell_id: str, t: float, resonance: float) -> Tuple[int,int]:
    """Small smooth drift using sin/cos; amplitude tied to resonance."""
    if not ENABLE_DRIFT:
        return (0,0)
    r = max(0.0, min(1.0, resonance))
    amp = 1.0 + 2.0*r  # 1..3 cells
    # different frequencies per cell
    kx = 0.6 + 0.5*(hsh(cell_id+"_kx", 100)/100.0)
    ky = 0.6 + 0.5*(hsh(cell_id+"_ky", 100)/100.0)
    dx = int(round(math.sin(t*kx + hsh(cell_id+"_px", 1000)/90.0)*amp))
    dy = int(round(math.cos(t*ky + hsh(cell_id+"_py", 1000)/110.0)*amp))
    return (dx, dy)

def place_cells_on_grid(cells: List[Tuple[str,int,float,float]], w: int, h: int, t: float) -> List[List[str]]:
    """
    Returns 2D char array representing the grid.
    Conflict resolution priority: user > repo > organic (by symbol order above).
    """
    # empty grid
    grid = [[" " for _ in range(w)] for _ in range(h)]
    # a parallel grid to track priority score
    prio = [[-1 for _ in range(w)] for _ in range(h)]

    def src_priority(cell_id: str) -> int:
        # higher number == higher priority
        if is_user_cell(cell_id): return 3
        if is_repo_cell(cell_id): return 2
        return 1

    for (cell_id, age, resonance, fitness) in cells:
        x0, y0 = base_position(cell_id, w, h)
        dx, dy = drift_offset(cell_id, t, resonance)
        x = max(0, min(w-1, x0 + dx))
        y = max(0, min(h-1, y0 + dy))

        col, sym = color_and_symbol(cell_id, fitness)
        # breathing shade swap for organic only
        if ENABLE_BREATH and not (is_user_cell(cell_id) or is_repo_cell(cell_id)):
            # use resonance to pick symbol intensity + breathing phase
            phase = _breath_phase
            shade = math.sin(phase*2*math.pi) * 0.5 + 0.5  # 0..1
            # blended thresholding
            if fitness > 0.75 and shade > 0.66:
                sym = STATUS["high"]
            elif fitness > 0.55 and shade > 0.33:
                sym = STATUS["med"]
            elif fitness > 0.35:
                sym = STATUS["low"]
            else:
                sym = STATUS["min"]

        p = src_priority(cell_id)
        if p >= prio[y][x]:
            prio[y][x] = p
            grid[y][x] = f"{col}{sym}{RESET}" if ENABLE_COLOR else sym

    return grid

# ========== SPARKLINE ==========
def render_sparkline(history: List[Tuple[int,int,float]]) -> str:
    if len(history) < 2:
        return ""
    populations = [h[1] for h in history]
    max_pop = max(populations) if populations else 1
    chars = "▁▂▃▄▅▆▇█"
    out = []
    for pop in populations:
        idx = int((pop / max_pop) * (len(chars) - 1)) if max_pop > 0 else 0
        out.append(chars[idx])
    return "".join(out)

# ========== RENDER ==========
def bell(n=1):
    if not ENABLE_SOUND: 
        return
    sys.stdout.write('\a'*n)
    sys.stdout.flush()

def draw_frame(conn: sqlite3.Connection,
               cells: List[Tuple[str,int,float,float]],
               iteration: int,
               metrics: Tuple[int,float,float,int,int],
               injected: List[Tuple[str,str,float,str]]|None,
               history: List[Tuple[int,int,float]]):
    """Full UI frame with grid, metrics and lists."""
    global _last_births, _last_deaths

    os.system("clear" if os.name != "nt" else "cls")

    cell_count, avg_resonance, avg_age, births, deaths = metrics

    # sound on change
    if births > _last_births:
        bell(1)
    if deaths > _last_deaths and cell_count > 0:
        bell(2)
    if cell_count == 0:
        bell(3)
    _last_births, _last_deaths = births, deaths

    # ===== Banner
    print(f"{BOLD}{COLORS['banner']}╔" + "═"*BANNER_WIDTH + f"╗{RESET}")
    print(f"{BOLD}{COLORS['banner']}║" + "⚡ ASYNC FIELD v6 ⚡".center(BANNER_WIDTH) + f"║{RESET}")
    print(f"{BOLD}{COLORS['banner']}╚" + "═"*BANNER_WIDTH + f"╝{RESET}")

    # ===== Metrics header (compact for mobile)
    print(f"I:{iteration} P:{cell_count} R:{avg_resonance:.2f}")
    print(f"Age:{avg_age:.1f} B:{births} D:{deaths}")

    # ===== Resonance pulse bar (compact)
    pw = int(max(0, min(1, avg_resonance))*20)
    pulse_bar = COLORS["high"] + "█"*pw + RESET + "░"*(20-pw)
    print(f"Pulse: {pulse_bar}")

    # ===== Sparkline (compact)
    spark = render_sparkline(history)
    if spark:
        print(f"Hist: {COLORS['medium']}{spark}{RESET}")

    # ===== Injections summary
    if injected:
        user_inj = [i for i in injected if i[3]=="user"]
        repo_inj = [i for i in injected if i[3]=="repo"]
        if user_inj:
            print(f"\n{COLORS['user']}★ You:{RESET}")
            for w, act, fit, _ in user_inj:
                sym = "★" if act=="BORN" else "↑"
                print(f"  {sym} {w} ({fit:.2f})")
        if repo_inj:
            print(f"\n{COLORS['repo']}◆ Repo:{RESET}")
            for w, act, fit, _ in repo_inj:
                sym = "◆" if act=="BORN" else "↑"
                print(f"  {sym} {w} ({fit:.2f})")

    # ===== GRID (life in semantic space)
    # update breathing phase bound to avg_resonance for tempo
    # (higher resonance -> faster breathing)
    tempo = 0.5 + avg_resonance*1.5  # 0.5..2.0 cycles per second
    # _breath_phase updated in the animation loop; here we just render

    grid = place_cells_on_grid(cells, GRID_W, GRID_H, time.time()*0.6)

    print("\n" + (" " * GRID_PADDING_LEFT) + DIM + "— semantic life grid —" + RESET)
    for row in grid:
        line = "".join(row)
        print((" " * GRID_PADDING_LEFT) + line)

    # ===== List (top cells)
    print("\n" + "─"*BANNER_WIDTH)
    if not cells:
        print(f"{COLORS['dead']}Field is empty. Type or commit!{RESET}\n")
    else:
        print(f"{'S':<3} {'WORD':<16} {'FIT':<5} {'RES':<5} {'AGE':<4}")
        print("─"*BANNER_WIDTH)
        for i, (cell_id, age, resonance, fitness) in enumerate(cells[:CELL_LIST_LIMIT]):
            col, sym = color_and_symbol(cell_id, fitness)
            # extract word
            word = cell_id
            if cell_id.startswith("user_") or cell_id.startswith("repo_"):
                parts = cell_id.split("_")
                if len(parts) > 1:
                    word = parts[1]
            word = (word[:16] + "…") if len(word) > 16 else word
            src = "U" if is_user_cell(cell_id) else ("R" if is_repo_cell(cell_id) else "O")
            print(f"{col}{sym}{RESET} {src:<2} {word:<16} {fitness:.2f}  {resonance:.2f}  {age:<4}")

    # ===== Footer / Legend & Prompt (compact)
    print("\n" + "─"*BANNER_WIDTH)
    print(f"{COLORS['user']}★{COLORS['repo']}◆{COLORS['high']}█{RESET} | {datetime.now().strftime('%H:%M')}")
    print(f"\n{COLORS['banner']}>:{RESET} ", end="", flush=True)

# ========== MAIN LOOP ==========
def main():
    global _running, _input_buffer, _breath_phase

    print(f"{BOLD}{COLORS['banner']}="*78 + RESET)
    print(f"{BOLD}{COLORS['banner']}  FIELD VISUALISER v6 — FULL GRID HYBRID".center(78) + RESET)
    print(f"{BOLD}{COLORS['banner']}="*78 + RESET)
    print(f"Database: {ACTIVE_DB}")
    print(f"Repo: {REPO_PATH}")

    repo_monitor = init_repo_monitor()
    if repo_monitor:
        print(f"{COLORS['repo']}✓ Repo monitor ACTIVE — tracking changes!{RESET}")
    else:
        print(f"{COLORS['dead']}✗ Repo monitor disabled{RESET}")

    print(f"\n{COLORS['user']}💬 Type messages to inject YOUR words{RESET}")
    print(f"{COLORS['repo']}📁 Repo changes auto-injected every cycle{RESET}\n")
    print("Starting in 3 seconds...\n")
    time.sleep(3)

    # Start input thread
    threading.Thread(target=input_thread, daemon=True).start()

    conn = sqlite3.connect(ACTIVE_DB)

    # time aggregation for UI refresh vs breathing
    last_refresh = 0.0
    try:
        while _running:
            now = time.time()
            # breathing tempo; we approximate with a fixed delta time tick
            # progress phase (wrap 0..1)
            _breath_phase = (_breath_phase + FRAME_DT) % 1.0

            # Every UI_REFRESH seconds: refetch state, render full frame
            if now - last_refresh >= UI_REFRESH:
                injected: List[Tuple[str,str,float,str]] = []

                # process user input
                if _input_buffer:
                    user_text = _input_buffer.pop(0)
                    words = extract_words(user_text)
                    if words:
                        inj = inject_words_into_field(conn, words, source="user")
                        injected.extend(inj)

                # process repo changes
                if repo_monitor:
                    repo_words = fetch_repo_changes(repo_monitor)
                    if repo_words:
                        inj = inject_words_into_field(conn, repo_words, source="repo")
                        injected.extend(inj)

                # fetch & render
                iteration, cell_count, avg_res, avg_age, births, deaths = fetch_state(conn)
                cells = fetch_cells(conn, limit=GRID_W*GRID_H)  # plenty
                hist = fetch_history(conn, limit=20)

                draw_frame(conn, cells, iteration,
                           (cell_count, avg_res, avg_age, births, deaths),
                           injected if injected else None,
                           hist)

                last_refresh = now

            # inner animation tick — just sleep short for smooth breathing
            time.sleep(FRAME_DT)

    except KeyboardInterrupt:
        _running = False
        print(f"\n\n{COLORS['banner']}Field visualisation stopped. 🧬⚡{RESET}\n")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
