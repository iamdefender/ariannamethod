#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIELD VISUALISER v7.4.1 — FULL (Termux / macOS / Linux)

Fixes vs 7.1:
- Banner never breaks (no emojis in box line, exact inner width, ANSI-safe)
- Perfect symmetry for metrics (fixed-width fields)
- Grid centered within banner width/terminal
- Input prompt always starts at column 0 (`> `)
- Kept ALL features: repo monitor, drift, breath, history sparkline, colors, sound, injections

Run:
  python field_visualiser.py
"""

import time
import sqlite3
import os
import random
import sys
import threading
import re
import math
import shutil
from datetime import datetime
from typing import List, Tuple, Dict, Optional
from pathlib import Path
from hashlib import blake2b

# ===================== ADAPTIVE CONFIG =====================
def get_terminal_config() -> Dict[str, int | bool]:
    try:
        term_w, term_h = shutil.get_terminal_size((80, 24))
    except Exception:
        term_w, term_h = 80, 24

    is_mobile = term_w < 70

    banner_w = max(56, min(96, int(term_w * 0.9)))  # чётная, безопасная ширина рамки
    # принудительно чётная ширина, чтобы «╔═...═╗» не уходил на переносах экзот. терминалов
    if banner_w % 2 == 1:
        banner_w -= 1

    grid_w = 36 if is_mobile else 52
    grid_h = 12 if is_mobile else 18
    pulse_bar_w = 24 if is_mobile else 40
    cell_list_limit = 3 if is_mobile else 6

    return {
        "term_w": term_w,
        "term_h": term_h,
        "is_mobile": is_mobile,
        "banner_width": banner_w,
        "grid_w": grid_w,
        "grid_h": grid_h,
        "pulse_bar_w": pulse_bar_w,
        "cell_list_limit": cell_list_limit,
    }

CFG = get_terminal_config()
TERM_W: int = CFG["term_w"]
TERM_H: int = CFG["term_h"]
IS_MOBILE: bool = CFG["is_mobile"]
BANNER_WIDTH: int = CFG["banner_width"]      # полная ширина рамки (включая ╔ ╗)
GRID_W: int = CFG["grid_w"]
GRID_H: int = CFG["grid_h"]
PULSE_BAR_W: int = CFG["pulse_bar_w"]
CELL_LIST_LIMIT: int = CFG["cell_list_limit"]

# ===================== DB/REPO CONFIG =====================
DB_PATH = "/data/data/com.termux/files/home/ariannamethod/resonance.sqlite3"
DB_PATH_LOCAL = "./field_test.sqlite3"
ACTIVE_DB = DB_PATH if os.path.exists(os.path.expanduser(DB_PATH)) else DB_PATH_LOCAL

REPO_PATH = Path(__file__).parent.parent.parent  # root проекта
ENABLE_REPO_MONITOR = True

# ===================== LOOP TIMING =====================
FRAME_DT = 0.2       # частота «дыхания»/дрейфа
UI_REFRESH = 5.0     # обновление UI каждые N секунд

# ===================== FLAGS =====================
ENABLE_COLOR = True
ENABLE_SOUND = True
ENABLE_BREATH = True
ENABLE_DRIFT = True

# ===================== COLORS =====================
RESET = "\033[0m" if ENABLE_COLOR else ""
BOLD  = "\033[1m" if ENABLE_COLOR else ""
DIM   = "\033[2m" if ENABLE_COLOR else ""
COLORS = {
    "high":   "\033[92m" if ENABLE_COLOR else "",
    "medium": "\033[93m" if ENABLE_COLOR else "",
    "low":    "\033[90m" if ENABLE_COLOR else "",
    "dead":   "\033[91m" if ENABLE_COLOR else "",
    "banner": "\033[95m" if ENABLE_COLOR else "",
    "user":   "\033[96m" if ENABLE_COLOR else "",
    "repo":   "\033[94m" if ENABLE_COLOR else "",
    "white":  "\033[97m" if ENABLE_COLOR else "",
}

# ===================== SYMBOLS =====================
STATUS = {
    "high":  "█",
    "med":   "▓",
    "low":   "▒",
    "min":   "░",
    "dead":  "·",
    "user":  "★",
    "repo":  "◆",
}

# ===================== STATE =====================
_last_births = 0
_last_deaths = 0
_user_words: List[str] = []
_repo_words: List[str] = []
_input_buffer: List[str] = []
_running = True
_breath_phase = 0.0

# ===================== REPO MONITOR =====================
try:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "arianna_core_utils"))
    from repo_monitor import RepoMonitor
    REPO_MONITOR_AVAILABLE = True
except Exception:
    REPO_MONITOR_AVAILABLE = False

def init_repo_monitor() -> Optional["RepoMonitor"]:
    if not REPO_MONITOR_AVAILABLE or not ENABLE_REPO_MONITOR:
        return None
    try:
        return RepoMonitor(repo_path=REPO_PATH)
    except Exception as e:
        print(f"⚠️  Repo monitor init failed: {e}")
        return None

def fetch_repo_changes(monitor) -> List[str]:
    if not monitor:
        return []
    try:
        changes = monitor.fetch_repo_context(limit=5)
        words: List[str] = []
        for ch in changes:
            content = ch.get('content', '')
            extracted = extract_words(content)
            words.extend(extracted[:3])
        # уникализируем до 10 слов
        out, seen = [], set()
        for w in words:
            if w not in seen:
                seen.add(w)
                out.append(w)
            if len(out) >= 10:
                break
        return out
    except Exception:
        return []

# ===================== WORDS =====================
STOP_WORDS = {
    "the","is","are","was","were","be","been","being","have","has","had","do","does","did",
    "will","would","could","should","may","might","must","can","this","that","with","from",
    "for","not","but","and","or","into","onto","over","under","between","within","out"
}

def extract_words(text: str) -> List[str]:
    words = re.findall(r'\b[a-z]{2,}\b', text.lower())
    return [w for w in words if w not in STOP_WORDS and len(w) > 2][:32]

# ===================== DB INJECTION =====================
def inject_words_into_field(conn: sqlite3.Connection, words: List[str], source: str = "user") -> List[Tuple]:
    cursor = conn.cursor()
    ts = int(time.time())
    injected: List[Tuple[str,str,float,str]] = []

    for word in words:
        cursor.execute("""
            SELECT cell_id, COALESCE(fitness,0.5) FROM field_cells
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

# ===================== INPUT THREAD =====================
def input_thread():
    global _running, _input_buffer
    while _running:
        try:
            # ВАЖНО: никаких префиксных пробелов, чтобы '>' всегда в колонке 0
            user_input = input()
            if user_input.strip():
                _input_buffer.append(user_input.strip())
        except (EOFError, KeyboardInterrupt):
            _running = False
            break

# ===================== DB FETCH =====================
def fetch_state(conn: sqlite3.Connection) -> Tuple[int,int,float,float,int,int]:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT iteration, cell_count, avg_resonance, avg_age, births, deaths
        FROM field_state ORDER BY id DESC LIMIT 1
    """)
    row = cursor.fetchone()
    return row if row else (0,0,0.0,0.0,0,0)

def fetch_cells(conn: sqlite3.Connection, limit: int = 120) -> List[Tuple[str,int,float,float]]:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cell_id, age, COALESCE(resonance_score,0.0), COALESCE(fitness,0.0)
        FROM field_cells WHERE status='alive'
        ORDER BY id DESC LIMIT ?
    """, (limit,))
    return cursor.fetchall()

def fetch_history(conn: sqlite3.Connection, limit: int = 20) -> List[Tuple[int,int,float]]:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT iteration, cell_count, avg_resonance
        FROM field_state ORDER BY id DESC LIMIT ?
    """, (limit,))
    return list(reversed(cursor.fetchall()))

# ===================== COLOR/SYMBOL PICK =====================
def is_user_cell(cell_id: str) -> bool:
    return cell_id.startswith("user_") or any(w in cell_id for w in _user_words)

def is_repo_cell(cell_id: str) -> bool:
    return cell_id.startswith("repo_") or any(w in cell_id for w in _repo_words)

def color_and_symbol(cell_id: str, fitness: float) -> Tuple[str, str]:
    if is_user_cell(cell_id):
        return COLORS["user"], STATUS["user"]
    if is_repo_cell(cell_id):
        return COLORS["repo"], STATUS["repo"]
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

# ===================== GRID / POSITIONING =====================
def hsh(s: str, mod: int) -> int:
    return int.from_bytes(blake2b(s.encode("utf-8"), digest_size=8).digest(), "little") % max(1, mod)

def base_position(cell_id: str, w: int, h: int) -> Tuple[int,int]:
    return hsh(cell_id+"_x", w), hsh(cell_id+"_y", h)

def drift_offset(cell_id: str, t: float, resonance: float) -> Tuple[int,int]:
    if not ENABLE_DRIFT:
        return (0,0)
    r = max(0.0, min(1.0, resonance))
    amp = 1.0 + 2.0*r
    kx = 0.6 + 0.5*(hsh(cell_id+"_kx", 100)/100.0)
    ky = 0.6 + 0.5*(hsh(cell_id+"_ky", 100)/100.0)
    dx = int(round(math.sin(t*kx + hsh(cell_id+"_px", 1000)/90.0)*amp))
    dy = int(round(math.cos(t*ky + hsh(cell_id+"_py", 1000)/110.0)*amp))
    return (dx, dy)

def place_cells_on_grid(cells: List[Tuple[str,int,float,float]], w: int, h: int, t: float) -> List[List[str]]:
    grid = [[" " for _ in range(w)] for _ in range(h)]
    prio = [[-1 for _ in range(w)] for _ in range(h)]

    def src_priority(cell_id: str) -> int:
        if is_user_cell(cell_id): return 3
        if is_repo_cell(cell_id): return 2
        return 1

    for (cell_id, age, resonance, fitness) in cells:
        x0, y0 = base_position(cell_id, w, h)
        dx, dy = drift_offset(cell_id, t, resonance)
        x = max(0, min(w-1, x0 + dx))
        y = max(0, min(h-1, y0 + dy))

        col, sym = color_and_symbol(cell_id, fitness)

        # breathing только для «органических» (не user/repo)
        if ENABLE_BREATH and not (is_user_cell(cell_id) or is_repo_cell(cell_id)):
            shade = math.sin(_breath_phase*2*math.pi) * 0.5 + 0.5
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

# ===================== SPARKLINE =====================
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

# ===================== LAYOUT HELPERS =====================
def clear_screen():
    # абсолютная очистка + перенос курсора
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()

def center_padding(total_width: int, inner_width: int) -> int:
    if inner_width >= total_width:
        return 0
    return (total_width - inner_width) // 2

def build_banner_lines(title: str, width: int) -> List[str]:
    """
    width — полная ширина рамки. Внутренняя ширина = width - 2.
    ВАЖНО: в строках рамки — только ASCII (никаких эмодзи), чтобы терминалы не роняли выравнивание.
    """
    inner = max(10, width - 2)
    top =  f"{BOLD}{COLORS['banner']}╔" + "═"*inner + f"╗{RESET}"
    mid =  f"{BOLD}{COLORS['banner']}║{RESET}" + title.center(inner) + f"{BOLD}{COLORS['banner']}║{RESET}"
    bot =  f"{BOLD}{COLORS['banner']}╚" + "═"*inner + f"╝{RESET}"
    return [top, mid, bot]

def bell(n=1):
    if not ENABLE_SOUND:
        return
    sys.stdout.write('\a'*n)
    sys.stdout.flush()

def safe_print_line(line: str):
    """
    Печатает строку без невидимых префиксных пробелов до рамки/грида/промпта.
    Никаких лишних отступов слева — чтобы ввод начинался строго с 0 колонки.
    """
    sys.stdout.write(line + "\n")

# ===================== DRAW =====================
def draw_frame(conn: sqlite3.Connection,
               cells: List[Tuple[str,int,float,float]],
               iteration: int,
               metrics: Tuple[int,float,float,int,int],
               injected: Optional[List[Tuple[str,str,float,str]]],
               history: List[Tuple[int,int,float]]) -> None:
    global _last_births, _last_deaths

    clear_screen()

    cell_count, avg_res, avg_age, births, deaths = metrics

    if births > _last_births:
        bell(1)
    if deaths > _last_deaths and cell_count > 0:
        bell(2)
    if cell_count == 0:
        bell(3)
    _last_births, _last_deaths = births, deaths

    # -------- Banner --------
    banner = build_banner_lines("ASYNC FIELD FOREVER — VISUALISER", BANNER_WIDTH)
    pad = center_padding(TERM_W, BANNER_WIDTH)
    for line in banner:
        safe_print_line(" " * pad + line)

    # -------- Metrics (strict columns; no spill) --------
    # widths: Iter(6) Pop(6) Res(6) | Age(6) Births(6) Deaths(6)
    m1 = f"Iter:{iteration:<6d}  Pop:{cell_count:<6d}  Res:{avg_res:<6.2f}"
    m2 = f"Age:{avg_age:<6.1f}  Births:{births:<6d}  Deaths:{deaths:<6d}"
    safe_print_line(" " * pad + m1)
    safe_print_line(" " * pad + m2)

    # -------- Pulse bar & history --------
    pw = int(max(0, min(1, avg_res))*PULSE_BAR_W)
    pulse_bar = COLORS["high"] + "█"*pw + RESET + "░"*(PULSE_BAR_W - pw)
    safe_print_line(" " * pad + f"Pulse: {pulse_bar}")

    spark = render_sparkline(history)
    if spark:
        safe_print_line(" " * pad + f"Hist:  {COLORS['medium']}{spark}{RESET}")

    # -------- Injections (show max 2 per source) --------
    if injected:
        user_inj = [i for i in injected if i[3] == "user"][:2]
        repo_inj = [i for i in injected if i[3] == "repo"][:2]
        if user_inj:
            safe_print_line(" " * pad + f"{COLORS['user']}★ You:{RESET}")
            for w, act, fit, _ in user_inj:
                sym = "★" if act == "BORN" else "↑"
                safe_print_line(" " * pad + f"  {sym} {w} ({fit:.2f})")
        if repo_inj:
            safe_print_line(" " * pad + f"{COLORS['repo']}◆ Repo:{RESET}")
            for w, act, fit, _ in repo_inj:
                sym = "◆" if act == "BORN" else "↑"
                safe_print_line(" " * pad + f"  {sym} {w} ({fit:.2f})")

    # -------- Grid (centered) --------
    grid = place_cells_on_grid(cells, GRID_W, GRID_H, time.time()*0.6)
    grid_pad = center_padding(TERM_W, GRID_W)
    # подпись
    safe_print_line(" " * (pad if pad > grid_pad else grid_pad) + DIM + "-- grid --" + RESET)
    for row in grid:
        line = "".join(row)
        safe_print_line(" " * grid_pad + line)

    # -------- Cell list (compact) --------
    sep = "—"*BANNER_WIDTH
    safe_print_line(" " * pad + sep)
    if not cells:
        safe_print_line(" " * pad + f"{COLORS['dead']}Empty. Type to bring Field to life.{RESET}")
    else:
        shown = 0
        for cell_id, age, resonance, fitness in cells:
            if shown >= CELL_LIST_LIMIT:
                break
            col, sym = color_and_symbol(cell_id, fitness)
            # показываем «слово»
            if cell_id.startswith("user_") or cell_id.startswith("repo_"):
                parts = cell_id.split("_")
                word = parts[1] if len(parts) > 1 else cell_id[:12]
            else:
                word = cell_id[:12]
            word = (word[:12] + "…") if len(word) > 12 else word
            src = "U" if is_user_cell(cell_id) else ("R" if is_repo_cell(cell_id) else "O")
            safe_print_line(" " * pad + f"{col}{sym}{RESET} {src} {word:<12} fit:{fitness:>5.2f} res:{resonance:>5.2f} age:{age:>3d}")
            shown += 1

    # -------- Footer + Prompt (strict at col 0) --------
    safe_print_line(" " * pad + sep)
    legend = f"{COLORS['user']}★{RESET} your  {COLORS['repo']}◆{RESET} repo  {COLORS['high']}█{RESET} organic"
    tm = datetime.now().strftime('%H:%M:%S')
    safe_print_line(" " * pad + f"{legend}  |  {tm}")
    # ВАЖНО: ввод всегда на 0 колонке — печатаем prompt без отступов.
    sys.stdout.write(f"\n{COLORS['banner']}>{RESET} ")
    sys.stdout.flush()

# ===================== MAIN =====================
def main():
    global _running, _input_buffer, _breath_phase

    # Стартовая «шапка» без рамки — чтобы не ловить Unicode ширину в первых строках
    title = "FIELD VISUALISER v7.4.1 — FULL"
    pad = center_padding(TERM_W, len(title))
    clear_screen()
    safe_print_line(" " * pad + BOLD + COLORS["banner"] + title + RESET)
    safe_print_line("")
    safe_print_line(f"Terminal: {TERM_W}x{TERM_H}  |  Mode: {'Mobile' if IS_MOBILE else 'Desktop'}")
    safe_print_line(f"Banner: {BANNER_WIDTH}  Grid: {GRID_W}x{GRID_H}  PulseBar: {PULSE_BAR_W}")

    repo_monitor = init_repo_monitor()
    if repo_monitor:
        safe_print_line(f"{COLORS['repo']}✓ Repo monitor active{RESET}")
    else:
        safe_print_line(f"{COLORS['dead']}✗ Repo monitor disabled{RESET}")

    safe_print_line(f"{COLORS['user']}Type to inject words into Field{RESET}")
    safe_print_line("Starting in 3s...")
    time.sleep(3)

    threading.Thread(target=input_thread, daemon=True).start()
    conn = sqlite3.connect(ACTIVE_DB)

    last_refresh = 0.0
    try:
        while _running:
            now = time.time()
            _breath_phase = (_breath_phase + FRAME_DT) % 1.0

            if now - last_refresh >= UI_REFRESH:
                injected: List[Tuple[str,str,float,str]] = []

                if _input_buffer:
                    user_text = _input_buffer.pop(0)
                    words = extract_words(user_text)
                    if words:
                        inj = inject_words_into_field(conn, words, source="user")
                        injected.extend(inj)

                if repo_monitor:
                    repo_words = fetch_repo_changes(repo_monitor)
                    if repo_words:
                        inj = inject_words_into_field(conn, repo_words, source="repo")
                        injected.extend(inj)

                iteration, cell_count, avg_res, avg_age, births, deaths = fetch_state(conn)
                cells = fetch_cells(conn, limit=GRID_W*GRID_H)
                hist = fetch_history(conn, limit=20)

                draw_frame(conn, cells, iteration,
                           (cell_count, avg_res, avg_age, births, deaths),
                           injected if injected else None,
                           hist)

                last_refresh = now

            time.sleep(FRAME_DT)

    except KeyboardInterrupt:
        _running = False
        sys.stdout.write(f"\n\n{COLORS['banner']}Stopped. 🧬⚡{RESET}\n")
        sys.stdout.flush()
    finally:
        conn.close()

if __name__ == "__main__":
    main()