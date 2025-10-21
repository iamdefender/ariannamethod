#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIELD VISUALISER v7.8 — HYBRID + WORD SPRITES
(One top line, no box; words + stars kept; centered grid)
"""

import os, re, sys, math, time, sqlite3, random, shutil, threading
from datetime import datetime
from hashlib import blake2b
from pathlib import Path
from typing import List, Tuple, Optional

# ---------------- CONFIG ----------------
DB_PATH = "/data/data/com.termux/files/home/ariannamethod/resonance.sqlite3"
DB_PATH_LOCAL = "./resonance.sqlite3"
ACTIVE_DB = DB_PATH if os.path.exists(os.path.expanduser(DB_PATH)) else DB_PATH_LOCAL

REPO_PATH = (Path(__file__).resolve().parents[2]
             if len(Path(__file__).parents) >= 2 else Path.cwd())
ENABLE_REPO_MONITOR = True

FRAME_DT   = 0.18        # drift tick
UI_REFRESH = 5.0         # DB poll rate
H_MARGIN   = 2
V_MARGIN   = 1

ENABLE_COLORS = True
ENABLE_BREATH = True
ENABLE_DRIFT  = True

# --------------- COLORS -----------------
RESET = "\033[0m" if ENABLE_COLORS else ""
BOLD  = "\033[1m" if ENABLE_COLORS else ""
DIM   = "\033[2m" if ENABLE_COLORS else ""

def C(s): return s if ENABLE_COLORS else ""

COL = {
    "title":  C("\033[95m"),
    "user":   C("\033[96m"),
    "repo":   C("\033[94m"),
    "high":   C("\033[92m"),
    "med":    C("\033[93m"),
    "low":    C("\033[90m"),
    "dead":   C("\033[91m"),
    "text":   C("\033[97m")
}

SYM = {"user":"★","repo":"◆","high":"█","med":"▓","low":"▒","min":"░","dead":"·"}

# --------------- STATE ------------------
_user_words: List[str] = []
_repo_words: List[str] = []
_input_buffer: List[str] = []
_running = True
_breath   = 0.0
_last_births = 0
_last_deaths = 0

# --------- TERMINAL HELPERS ------------
def term_size() -> Tuple[int,int]:
    try:
        w,h = shutil.get_terminal_size((80, 24))
    except Exception:
        w,h = 80,24
    return max(60,w), max(22,h)

def clear_screen():
    sys.stdout.write("\033c"); sys.stdout.flush()

def center_x(inner_w: int, total_w: int) -> int:
    return max(H_MARGIN, (total_w - inner_w)//2)

def crop(s: str, w: int) -> str:
    return s if len(s) <= w else s[:max(0,w-1)] + "…"

# ------------- REPO MONITOR ------------
def try_init_repo_monitor():
    if not ENABLE_REPO_MONITOR:
        return None
    try:
        sys.path.insert(0, str(REPO_PATH / "arianna_core_utils"))
        from repo_monitor import RepoMonitor
        return RepoMonitor(repo_path=REPO_PATH)
    except Exception:
        return None

STOP = {
    "the","is","are","was","were","be","been","being",
    "have","has","had","do","does","did","will","would",
    "could","should","may","might","must","can","this","that",
    "with","from","for","not","but","and","or","into","onto",
    "over","under","between","within","out","your","you","our"
}
def extract_words(text: str) -> List[str]:
    words = re.findall(r"[a-zA-Z]{2,}", text.lower())
    return [w for w in words if w not in STOP and len(w)>2]

def fetch_repo_words(monitor) -> List[str]:
    if not monitor: return []
    try:
        changes = monitor.detect_changes()
        bag = []
        # Extract words from modified file paths
        for fpath in list(changes.get('modified', []))[:5]:
            # Get filename words (e.g., "consilium_agent.py" -> ["consilium", "agent"])
            bag += extract_words(str(fpath))
        for fpath in list(changes.get('added', []))[:3]:
            bag += extract_words(str(fpath))

        seen, out = set(), []
        for w in bag:
            if w not in seen and len(w) > 3:
                seen.add(w); out.append(w)
            if len(out) >= 10: break
        return out
    except Exception as e:
        return []

# ---------------- DB LAYER --------------
def db_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(ACTIVE_DB)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def fetch_state(conn) -> Tuple[int,int,float,float,int,int]:
    cur = conn.cursor()
    cur.execute("""SELECT iteration, cell_count, avg_resonance, avg_age, births, deaths
                   FROM field_state ORDER BY id DESC LIMIT 1""")
    row = cur.fetchone()
    return row if row else (0,0,0.0,0.0,0,0)

def fetch_cells(conn, limit:int) -> List[Tuple[str,int,float,float]]:
    cur = conn.cursor()
    cur.execute("""SELECT cell_id, COALESCE(age,0), COALESCE(resonance_score,0.0), COALESCE(fitness,0.0)
                   FROM field_cells WHERE status='alive' ORDER BY id DESC LIMIT ?""",(limit,))
    return cur.fetchall()

def fetch_history(conn, limit:int=18) -> List[Tuple[int,int,float]]:
    cur = conn.cursor()
    cur.execute("""SELECT iteration, cell_count, avg_resonance
                   FROM field_state ORDER BY id DESC LIMIT ?""",(limit,))
    rows = cur.fetchall(); rows.reverse(); return rows

def inject_words(conn, words: List[str], source="user") -> List[Tuple[str,str,float,str]]:
    cur = conn.cursor(); ts = int(time.time()); out=[]
    for w in words:
        cur.execute("""SELECT cell_id, COALESCE(fitness,0.6) FROM field_cells
                       WHERE status='alive' AND cell_id LIKE ? ORDER BY id DESC LIMIT 1""",
                    (f"%{w}%",))
        hit = cur.fetchone()
        if hit:
            cid, old = hit; new = min(1.0, old+0.15)
            cur.execute("UPDATE field_cells SET fitness=? WHERE cell_id=? AND status='alive'",(new,cid))
            out.append((w,"BOOSTED",new,source))
        else:
            cid = f"{source}_{w}_{ts}"
            fit = random.uniform(0.65,0.85) if source=="repo" else random.uniform(0.6,0.9)
            res = random.uniform(0.5,0.8)
            cur.execute("""INSERT INTO field_cells(cell_id, age, resonance_score, fitness, status, timestamp)
                           VALUES (?,0,?,?, 'alive', ?)""",(cid,res,fit,ts))
            out.append((w,"BORN",fit,source))
            (_user_words if source=="user" else _repo_words).append(w)
    conn.commit(); return out

# ---------------- INPUT -----------------
def input_thread():
    global _running, _input_buffer
    while _running:
        try:
            line = input()
            if line.strip(): _input_buffer.append(line.strip())
        except (EOFError, KeyboardInterrupt):
            _running = False; break

# --------------- RENDER -----------------
def spark(history: List[Tuple[int,int,float]]) -> str:
    if len(history)<2: return ""
    pops = [h[1] for h in history]; mx = max(1,max(pops))
    chars = "▁▂▃▄▅▆▇█"
    return "".join(chars[int((p/mx)*(len(chars)-1))] for p in pops)

def color_symbol(cell_id: str, fitness: float) -> Tuple[str,str]:
    def has_any(bag): return any(w in cell_id for w in bag)
    if cell_id.startswith("user_") or has_any(_user_words): return (COL["user"], SYM["user"])
    if cell_id.startswith("repo_") or has_any(_repo_words): return (COL["repo"], SYM["repo"])
    if   fitness > 0.75: return (COL["high"], SYM["high"])
    elif fitness > 0.55: return (COL["med"],  SYM["med"])
    elif fitness > 0.35: return (COL["low"],  SYM["low"])
    elif fitness > 0.15: return (COL["low"],  SYM["min"])
    else:                return (COL["dead"], SYM["dead"])

def hsh(s: str, mod: int) -> int:
    if mod<=0: return 0
    return int.from_bytes(blake2b(s.encode(), digest_size=8).digest(), "little") % mod

def base_pos(cell_id: str, w:int, h:int) -> Tuple[int,int]:
    return hsh(cell_id+"_x", w), hsh(cell_id+"_y", h)

def drift_offset(cell_id: str, t: float, resonance: float) -> Tuple[int,int]:
    if not ENABLE_DRIFT: return (0,0)
    r = max(0.0, min(1.0, resonance)); amp = 1.0 + 2.0*r
    kx = 0.6 + (hsh(cell_id+"_kx",100)/200.0)
    ky = 0.6 + (hsh(cell_id+"_ky",100)/200.0)
    dx = int(round(math.sin(t*kx + hsh(cell_id+"_px",1000)/90.0) * amp))
    dy = int(round(math.cos(t*ky + hsh(cell_id+"_py",1000)/110.0) * amp))
    return dx,dy

def token_for_cell(cell_id: str) -> str:
    if "_" in cell_id:
        p = cell_id.split("_")
        if len(p)>=2 and p[1]: return p[1][:8]
    return re.sub(r"[^a-zA-Z0-9]","",cell_id)[:8] or "cell"

def put_text(grid: List[List[str]], x:int, y:int, token:str):
    h=len(grid); w=len(grid[0]) if h>0 else 0
    if y<0 or y>=h: return
    for i,ch in enumerate(token):
        xx=x+i
        if 0<=xx<w: grid[y][xx]=ch

def build_grid(cells, grid_w, grid_h, t):
    grid = [[" " for _ in range(grid_w)] for _ in range(grid_h)]
    for (cid, age, res, fit) in cells:
        col,sym = color_symbol(cid, fit)
        token   = token_for_cell(cid)
        if ENABLE_BREATH and not (cid.startswith("user_") or cid.startswith("repo_")):
            shade = math.sin(_breath*2*math.pi)*0.5+0.5
            if   fit>0.75 and shade>0.66: sym = SYM["high"]
            elif fit>0.55 and shade>0.33: sym = SYM["med"]
            elif fit>0.35:                 sym = SYM["low"]
            else:                          sym = SYM["min"]
        sprite = f"{col}{sym} {token}{RESET}" if ENABLE_COLORS else f"{sym} {token}"
        bx,by = base_pos(cid, grid_w, grid_h)
        dx,dy = drift_offset(cid, t, res)
        x = max(0,min(grid_w-1,bx+dx)); y = max(0,min(grid_h-1,by+dy))
        plain_len = 2 + len(token)
        if x + plain_len >= grid_w: x = max(0, grid_w - plain_len)
        put_text(grid, x, y, sprite)
    return grid

def pulse_bar(resonance: float, width:int) -> str:
    width = max(10,width)
    filled = int(max(0.0,min(1.0,resonance))*width)
    return f"{COL['high']}{'█'*filled}{RESET}{'░'*(width-filled)}"

def header_lines(w:int, it:int, pop:int, res:float, age:float, b:int, d:int) -> List[str]:
    items=[f"Iter:{it}",f"Pop:{pop}",f"Res:{res:.2f}",f"Age:{age:.1f}",f"Births:{b}",f"Deaths:{d}"]
    line=" | ".join(items)
    if len(line)<=w-2*H_MARGIN: return [line]
    mid=len(items)//2; return [" | ".join(items[:mid]), " | ".join(items[mid:])]

# -------------- FRAME -------------------
def draw_frame(conn, cells, it:int, pop:int, res:float, age:float, b:int, d:int,
               injected: Optional[List[Tuple[str,str,float,str]]], hist):
    global _last_births, _last_deaths

    W,H = term_size()
    title = "ASYNC FIELD FOREVER (HYBRID) — VISUALISER"
    line_w = max(50, W-8)  # На 8 символов короче ширины терминала
    left   = center_x(line_w, W)

    # layout
    grid_w = 44 if W<80 else 56
    grid_h = 10 if H<28 else 16
    grid_left = center_x(grid_w, W)

    clear_screen()

    # Title + single horizontal rule
    print(" "*left + f"{COL['title']}{BOLD}{title.center(line_w)}{RESET}")
    print(" "*left + "─"*line_w)

    for ln in header_lines(line_w, it, pop, res, age, b, d):
        print(" "*left + ln)

    print(" "*left + f"Pulse: {pulse_bar(res, max(18,int(line_w*0.45)))}")
    s = spark(hist)
    if s: print(" "*left + f"Hist:  {COL['med']}{s}{RESET}")

    print("\n" + " "*left + (DIM+"– grid –"+RESET).center(line_w))

    t = time.time()*0.6
    grid = build_grid(cells, grid_w, grid_h, t)
    for row in grid:
        print(" "*grid_left + "".join(row))

    # injections recap (compact)
    if injected:
        u=[i for i in injected if i[3]=="user"][:3]
        r=[i for i in injected if i[3]=="repo"][:3]
        if u or r: print()
        if u:
            print(" "*left + f"{COL['user']}★ You:{RESET} " +
                  ", ".join(f"{w} ({act.lower()})" for w,act,_,_ in u))
        if r:
            print(" "*left + f"{COL['repo']}◆ Repo:{RESET} " +
                  ", ".join(f"{w} ({act.lower()})" for w,act,_,_ in r))

    # mini list
    if cells:
        print()
        head="src  word          fit   res   age"
        print(" "*left + head); print(" "*left + "-"*line_w)
        for cid, age_c, res_c, fit_c in cells[:min(4,len(cells))]:
            col,sym = color_symbol(cid, fit_c)
            token = token_for_cell(cid)
            src = ("U" if cid.startswith("user_") else "R" if cid.startswith("repo_") else "O")
            print(" "*left + f"{col}{sym}{RESET} {src}  {token:<12}  {fit_c:0.2f}  {res_c:0.2f}  {age_c}")

    # footer + prompt
    print("\n" + " "*left + "-"*line_w)
    legend = f"{COL['user']}★ your{RESET}   {COL['repo']}◆ repo{RESET}   {COL['high']}█ organic{RESET}"
    clock  = datetime.now().strftime("%H:%M:%S")
    pad = max(1, line_w - len(legend) - len(clock) - 1)
    print(" "*left + legend + " "*pad + clock)

    print("\n" + " "*left + "> ", end="", flush=True)

    # beeps on change
    if b > _last_births: sys.stdout.write("\a")
    if d > _last_deaths and pop>0: sys.stdout.write("\a\a")
    if pop == 0: sys.stdout.write("\a\a\a")
    _last_births, _last_deaths = b, d

# --------------- MAIN -------------------
def main():
    global _running, _breath

    W,H = term_size()
    clear_screen()
    title = "FIELD VISUALISER v7.8 — HYBRID + WORD SPRITES"
    line_w = min(max(50,int(W*0.92)), W-2*H_MARGIN)
    left   = center_x(line_w, W)
    print(" "*left + f"{COL['title']}{BOLD}{title.center(line_w)}{RESET}")
    print(" "*left + "─"*line_w)
    print(" "*left + f"DB: {ACTIVE_DB}")
    monitor = try_init_repo_monitor()
    print(" "*left + (f"{COL['repo']}Repo monitor: ACTIVE{RESET}" if monitor else f"{COL['dead']}Repo monitor: OFF{RESET}"))
    print(" "*left + f"{COL['user']}Type text to inject words (e.g., 'hello field how are you'){RESET}")
    print(" "*left + "Starting in 3s...\n"); time.sleep(3)

    threading.Thread(target=input_thread, daemon=True).start()
    conn = db_conn()

    last_ui = 0.0
    injected_last = None

    try:
        while _running:
            now = time.time()
            _breath = (_breath + FRAME_DT) % 1.0

            injected_last = None
            if _input_buffer:
                text = _input_buffer.pop(0)
                words = extract_words(text)
                if words:
                    injected_last = inject_words(conn, words, source="user")

            if now - last_ui >= UI_REFRESH:
                if monitor:
                    rw = fetch_repo_words(monitor)
                    if rw:
                        inj = inject_words(conn, rw, source="repo")
                        injected_last = (injected_last or []) + inj

                it, pop, res, age, br, de = fetch_state(conn)
                cells = fetch_cells(conn, limit=120)
                hist  = fetch_history(conn, limit=18)
                draw_frame(conn, cells, it, pop, res, age, br, de, injected_last, hist)
                last_ui = now

            time.sleep(FRAME_DT)

    except KeyboardInterrupt:
        _running = False
        clear_screen()
        print(f"{COL['title']}Stopped. Async field forever. 🧬⚡{RESET}")
    finally:
        try: conn.close()
        except: pass

if __name__ == "__main__":
    main()