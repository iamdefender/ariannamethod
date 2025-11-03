#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

HOME_DIR="$HOME"
REPO_DIR="$HOME_DIR/ariannamethod"
BASE_DIR="$REPO_DIR/async_field_forever/field"
TARGET_DIR="$REPO_DIR/async_field_forever/field5"
DB_PATH="$REPO_DIR/resonance.sqlite3"

mkdir -p "$TARGET_DIR"

echo "[Field5] Baseline: $BASE_DIR"
echo "[Field5] Target  : $TARGET_DIR"

if [ -d "$BASE_DIR" ]; then
  echo "[Field5] Copying Field4 → Field5 sandbox..."
  cp -a "$BASE_DIR"/. "$TARGET_DIR"/
else
  echo "[Field5] ⚠️ Base Field directory not found: $BASE_DIR"
  echo "Create it first, then re-run this script."
  exit 1
fi

CFG="$TARGET_DIR/config.py"
if [ ! -f "$CFG" ]; then
  echo "[Field5] ⚠️ No config.py found at $CFG — creating minimal one"
  cat > "$CFG" <<'PY'
# Minimal config for Field5 (created by bootstrap)
INITIAL_POPULATION = 25
MAX_POPULATION = 100
DEATH_THRESHOLD = 0.3
REPRODUCTION_THRESHOLD = 0.65
MUTATION_RATE = 0.1
META_LEARNING_RATE = 0.05
TICK_DURATION = 5
PY
fi

echo "[Field5] Appending overrides to config.py"
cat >> "$CFG" <<'PY'

# ============================
# FIELD5 OVERRIDES (Sandbox)
# ============================
# Scheduling
UPDATE_ORDER = "random"   # reshuffle update order each tick
TICK_BARRIER = True       # compute next-state, then commit (avoid race-deaths)

# Ecology (prepared for chemostat)
ENERGY_INFLOW = 0.02      # baseline resource per tick
OUTFLOW_RATE  = 0.01      # soft global decay

# Population guards
NMIN = 10                 # minimal viable population
HOF_SIZE = 8              # hall-of-fame seed bank size
EXTINCTION_COOLDOWN = 5   # ticks before next resurrection
MAX_DF_DT = 0.6           # kill-switch if population drops >60%/tick

# Mode switch
FIELD_MODE = "cycles"     # or "steady"
PY

# Ensure metrics table exists
if [ -f "$DB_PATH" ]; then
  echo "[Field5] Ensuring field_metrics exists in resonance.sqlite3"
  sqlite3 "$DB_PATH" "CREATE TABLE IF NOT EXISTS field_metrics (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, iteration INTEGER, pop INTEGER, avg_res REAL, avg_age REAL, births INTEGER, deaths INTEGER, novelty REAL, niches INTEGER);"
else
  echo "[Field5] ℹ️ DB not found at $DB_PATH (will be created by the system when needed)"
fi

echo "[Field5] Done. Next: cd $TARGET_DIR && python3 -u field_core.py (or your launcher)"
